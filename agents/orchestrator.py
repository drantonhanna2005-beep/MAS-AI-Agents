"""المنسّق الذكي (Orchestrator) — التوجيه + الأدوات + RAG + البحث + البث المباشر.

مسار الرسالة:
1) نوايا حتمية (GPA/CV/روابط) → أدوات فورية + توجيه.
2) تصنيف LLM سريع (JSON) أو توجيه بالكلمات المفتاحية في الوضع المحلي.
3) استرجاع سياق RAG (+ بحث ويب اختياري) → تجميع السياق.
4) الوكيل الأساسي يجيب (تفكير عميق [[THINKING]] ثم [[ANSWER]]) + وكيل ثانٍ للأسئلة العميقة.
5) أحداث SSE مباشرة للواجهة + حفظ المصادر في السجل.
"""
from __future__ import annotations

import json
import re
from collections.abc import Generator

from core import rag, websearch, gpatool
from core.translate import quick_translate
from core.config import load_config, resolve_provider, provider_supports_vision, get_model_key
from core.llm import LLMError, stream_chat, complete
from .registry import AGENT_MAP, COMMON_RULES

TAG_THINK = "[[THINKING]]"
TAG_ANSWER = "[[ANSWER]]"

GPA_RE = re.compile(r"gpa|معدل|تراكمي|تقديرات|احسب.*درجات|حساب.*معدل", re.I)
CV_RE = re.compile(r"\bcv\b|سيرة|resume|ats", re.I)
_GRADE_TOKEN = re.compile(r"\b(A\+|A-|B\+|B-|C\+|C-|D\+|[A-F]|ممتاز|جيد جداً?|مقبول|ضعيف|راسب)\b", re.I)
GREETING_RE = re.compile(r"^\s*(?:هاي|هلا|هلو|أهلا|اهلا|أهلًا|اهلا وسهلا|مرحبا|مرحباً|السلام عليكم|وعليكم السلام|صباح الخير|مساء الخير|صباح النور|مساء النور|hi+|hello+|hey+|yo+|good\s+(?:morning|evening|afternoon|night)|bonjour|salut|bonsoir)[\s!?.،,~]*$", re.I)
SHORT_SMALLTALK_RE = re.compile(r"^\s*(?:شكرا|شكرًا|thanks|thank you|thx|ok|okay|تمام|ماشي|حسنا|حسنًا|yes|no|نعم|لا|ايوه|أيوه)[\s!?.،,~]*$", re.I)


def _classify_keywords(message: str) -> dict:
    text = message.lower()
    scores: dict[str, int] = {}
    for aid, a in AGENT_MAP.items():
        s = sum(1 for kw in a["keywords"] if kw in text)
        if s:
            scores[aid] = s
    ranked = sorted(scores.items(), key=lambda x: -x[1])
    agents = [aid for aid, _ in ranked[:2] if ranked]
    primary = agents[0] if agents else "research"
    if len(agents) < 2 or scores.get(agents[1], 0) < max(1, scores[primary] // 2):
        agents = [primary]
    deep = len(message) > 220 or any(w in text for w in ("قارن", "خطط", "لماذا", "اشرح بالتفصيل", "خطة"))
    return {"agents": agents, "complexity": "deep" if deep else "simple",
            "needs_rag": True, "needs_web": any(w in text for w in ("اليوم", "أحدث", "الآن", "سعر", "أسعار", "اخبار", "أخبار"))}


def _keywords_confident(message: str) -> bool:
    """توجيه فوري بالكلمات المفتاحية عندما يكون الفائز واضحاً — سرعة بدون LLM."""
    text = message.lower()
    scores: list[int] = []
    for a in AGENT_MAP.values():
        s = sum(1 for kw in a["keywords"] if kw in text)
        if s:
            scores.append(s)
    if not scores:
        return False
    scores.sort(reverse=True)
    return scores[0] >= 2 and (len(scores) == 1 or scores[0] >= scores[1] + 2)


def _classify_llm(message: str, cfg: dict, prov: dict) -> dict | None:
    router_model = (cfg.get("router_models") or {}).get(prov["provider"]) or prov["model"]
    system = (
        "أنت موجّه فريق وكلاء جامعي. صنّف رسالة المستخدم وأعد JSON فقط دون أي شرح، بالشكل:\n"
        '{"agents": ["..."], "complexity": "simple"|"deep", "needs_rag": true|false, "needs_web": true|false}\n'
        "الوكلاء: academic (مواد/لائحة/ساعات/تسجيل/جداول/أقسام), planner (خطط مذاكرة/تنظيم وقت), "
        "calc (GPA/نسب/تقديرات), finance (مصاريف/دفع/بنوك), campus (روابط/جروبات/درويفات/خدمات جامعية), "
        "housing (سكن/مناطق/خدمات قريبة في اسيوط الجديدة), career (CV/LinkedIn/عمل حر/تدريب), "
        "resources (كورسات/قنوات/منصات), research (أي موضوع عام/تحليل مرفقات).\n"
        "القواعد: وكيل أساسي واحد غالباً؛ أضف ثانوياً فقط إذا تلاقى مجالان واضحان. needs_rag=true لأي ما "
        "يخص الجامعة أو المواد أو الملفات أو الروابط. needs_web=true فقط لو لزم معلومات حديثة من الإنترنت."
    )
    try:
        _, content = complete(prov["provider"], router_model,
                              [{"role": "system", "content": system},
                               {"role": "user", "content": message[:2000]}],
                              api_key=get_model_key(prov["provider"], router_model, cfg),
                              ollama_url=cfg.get("ollama_url", ""), temperature=0.0)
        m = re.search(r"\{.*\}", content, re.S)
        if not m:
            return None
        data = json.loads(m.group(0))
        agents = [a for a in (data.get("agents") or []) if a in AGENT_MAP][: cfg.get("max_agents", 2)]
        if not agents:
            return None
        return {"agents": agents,
                "complexity": data.get("complexity") if data.get("complexity") in ("simple", "deep") else "simple",
                "needs_rag": bool(data.get("needs_rag", True)),
                "needs_web": bool(data.get("needs_web", False))}
    except Exception:
        return None


def parse_gpa_rows(message: str) -> list[dict]:
    rows: list[dict] = []
    for line in message.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if re.match(r"^\|?[\s:-]+(?:\|[\s:-]+)+\|?$", line):
            continue
        line = re.sub(r"^(?:[-*•]|\d+\.|\b)\s*", "", line)
        line = line.strip(" |")
        if not line:
            continue
        gm = _GRADE_TOKEN.search(line)
        if not gm:
            continue
        pre_text = line[:gm.start()].strip()
        post_text = line[gm.end():].strip()
        rem_text = f"{pre_text} {post_text}"
        hr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ساعات|ساعة|hours?|hrs?|h|cr)\b", rem_text, re.I)
        if hr_match:
            hours = float(hr_match.group(1))
        else:
            nums = re.findall(r"\d+(?:\.\d+)?", rem_text)
            if not nums:
                continue
            hours = float(nums[-1])
        if hours <= 0 or hours > 12:
            continue
        course = (line[:gm.start()].strip(" -|،:") or f"مادة {len(rows) + 1}")[:40]
        course = re.sub(r"\s*\d+(?:\.\d+)?\s*$", "", course).strip() or f"مادة {len(rows) + 1}"
        rows.append({"course": course, "hours": hours, "grade": gm.group(1)})
    return rows if len(rows) >= 2 else []


def _messages_for(agent_id: str, cfg: dict, user_block: str, tail: list[dict],
                  extra_context: str = "", secondary_of: str | None = None,
                  skip_tags: bool = False, lang: str = "ar") -> list[dict]:
    agent = AGENT_MAP[agent_id]
    system = agent["prompt"] + "\n" + COMMON_RULES
    if secondary_of:
        sec = AGENT_MAP[secondary_of]
        system += (f"\n\nمهمتك الآن: أضف إسهاماً متمماً بعد إجابة زميلك «{sec['name']}». ابدأ بعنوان "
                   f"«— إضافة من منظور {agent['name']} —» ثم نقاط عملية قصيرة فقط، ولا تكرر ما قاله الزميل "
                   "ولا تكرر التعريف بنفسك.")
    if cfg.get("deep_think", True) and not secondary_of and not skip_tags:
        system += (f"\n\nأسلوب الإخراج الإلزامي: ابدأ بالوسم {TAG_THINK} ثم فكّر بإيجاز وواقعية (تحليل السؤال، "
                   f"ما المطلوب، خطة الإجابة، ونقاط تحتاج تحققاً)، ثم الوسم {TAG_ANSWER} ثم الإجابة النهائية "
                   "المنظمة والمباشرة. لا تكتب أي شيء خارج هذين الجزأين.")
    if lang == "en":
        system += "\n\nMANDATORY ANSWER LANGUAGE: Write the ENTIRE answer in fluent, professional English."
    else:
        system += "\n\nلغة الإجابة الإلزامية: اكتب الإجابة بالكامل بالعربية الفصحى الواضحة."
    messages = [{"role": "system", "content": system}]
    for m in tail[-8:]:
        messages.append({"role": m["role"], "content": m["content"][:4000]})
    messages.append({"role": "user", "content": user_block + (("\n\n" + extra_context) if extra_context else "")})
    return messages


class _TagSplitter:
    """يفصل تدفق النموذج إلى thinking/content حسب الوسوم [[THINKING]]/[[ANSWER]]."""

    def __init__(self):
        self.mode: str | None = None
        self.buf = ""
        self.native_thinking = False

    def feed(self, kind: str, text: str) -> list[tuple[str, str]]:
        if kind == "thinking":
            self.native_thinking = True
            return [("thinking", text)]
        self.buf += text
        out: list[tuple[str, str]] = []
        keep = max(len(TAG_THINK), len(TAG_ANSWER)) - 1
        while True:
            if self.mode is None:
                i1, i2 = self.buf.find(TAG_THINK), self.buf.find(TAG_ANSWER)
                idx = min([i for i in (i1, i2) if i >= 0], default=-1)
                if idx < 0:
                    if len(self.buf) > keep:
                        out.append(("content", self.buf[:-keep]))
                        self.buf = self.buf[-keep:]
                    break
                if idx > 0:
                    out.append(("content", self.buf[:idx]))
                self.mode = "thinking" if idx == i1 or (i1 >= 0 and i1 < i2) else "content"
                self.buf = self.buf[idx + (len(TAG_THINK) if self.mode == "thinking" else len(TAG_ANSWER)):]
            else:
                tag = TAG_ANSWER if self.mode == "thinking" else TAG_THINK
                j = self.buf.find(tag)
                if j < 0:
                    if len(self.buf) > keep:
                        out.append((self.mode, self.buf[:-keep]))
                        self.buf = self.buf[-keep:]
                    break
                if j > 0:
                    out.append((self.mode, self.buf[:j]))
                self.mode = "content" if self.mode == "thinking" else "thinking"
                self.buf = self.buf[j + len(tag):]
        return out

    def flush(self) -> list[tuple[str, str]]:
        out = [(self.mode or "content", self.buf)] if self.buf else []
        self.buf = ""
        return out


def _chat_candidates(cfg: dict, prov: dict, model: str) -> list[tuple[str, str, str]]:
    """سلسلة تفاوض المزودات: الأساسي أولاً ثم بدائل مجانية تلقائية — حتى لا يتوقف الذكاء أبداً."""
    cands = [(prov["provider"], model, get_model_key(prov["provider"], model, cfg))]
    if prov["provider"] == "openrouter":
        for alt in ("google/gemma-4-26b-a4b-it:free", "google/gemma-4-31b-it:free"):
            if alt != model:
                k = get_model_key("openrouter", alt, cfg)
                if k:
                    cands.append(("openrouter", alt, k))
        gk = (cfg.get("api_keys") or {}).get("gemini", "")
        if gk:
            cands.append(("gemini", (cfg.get("stt") or {}).get("gemini_model") or "gemini-flash-lite-latest", gk))
    elif prov["provider"] in ("groq", "gemini"):
        ok = (cfg.get("api_keys") or {}).get("openrouter", "")
        if ok:
            cands.append(("openrouter", (cfg.get("main_models") or {}).get("openrouter") or "openrouter/free", ok))
        if prov["provider"] == "groq":
            gk = (cfg.get("api_keys") or {}).get("gemini", "")
            if gk:
                cands.append(("gemini", (cfg.get("stt") or {}).get("gemini_model") or "gemini-flash-lite-latest", gk))
    if prov["provider"] == "gemini":
        gk2 = (cfg.get("api_keys") or {}).get("gemini", "")
        if gk2:
            for alt_g in ("gemini-flash-lite-latest", "gemini-3.6-flash", "gemini-3-flash"):
                if alt_g != model and not any(c[0] == "gemini" and c[1] == alt_g for c in cands):
                    cands.append(("gemini", alt_g, gk2))
    # مع صور: اقتصر البدائل على نماذج قادرة على الرؤية (وإلا ادّعى نموذج نصي أنه "لا يرى")
    if prov.get("vision_model"):
        cands = [c for c in cands if provider_supports_vision(c[0], c[1])]
        # بدائل Gemini الرؤيوية: النموذج الأساسي قد لا يتاح للمفتاح (404) → جرّب التالي تلقائياً
        gk = (cfg.get("api_keys") or {}).get("gemini", "")
        if gk and prov["provider"] == "gemini":
            for alt_g in ("gemini-flash-lite-latest", "gemini-3.6-flash", "gemini-3-flash", "gemini-3-pro"):
                if alt_g != model and not any(c[0] == "gemini" and c[1] == alt_g for c in cands):
                    cands.append(("gemini", alt_g, gk))
        ok = (cfg.get("api_keys") or {}).get("openrouter", "")
        if ok and not any(c[0] == "openrouter" for c in cands):
            for alt in ("google/gemma-4-26b-a4b-it:free", "meta-llama/llama-4-scout:free"):
                k = get_model_key("openrouter", alt, cfg)
                if k: cands.append(("openrouter", alt, k))
    # إزالة التكرار مع الحفاظ على الترتيب
    seen: set = set()
    out = []
    for c in cands:
        if c[:2] in seen:
            continue
        seen.add(c[:2])
        out.append(c)
    return out


def _stream_agent(agent_id: str, cfg: dict, prov: dict, user_block: str,
                  tail: list[dict], extra_context: str = "", secondary_of: str | None = None,
                  images: list[str] | None = None, acc: dict | None = None,
                  lang: str = "ar") -> Generator[dict, None, None]:
    """بث حي لإجابة وكيل واحد مع سلسلة تفاوض تلقائية بين المزودات عند 429/5xx/مفتاح تالف."""
    acc = acc if acc is not None else {"thinking": "", "content": ""}
    model = prov.get("vision_model") or prov.get("model") or (cfg.get("main_models") or {}).get(prov.get("provider", ""), "")
    splitter = _TagSplitter()
    last_err: LLMError | None = None
    for prov_name, model_i, key_i in _chat_candidates(cfg, prov, model):
        skip_tags = any(k in (model_i or "").lower() for k in ("r1", "thinking", "qwq"))
        messages = _messages_for(agent_id, cfg, user_block, tail, extra_context, secondary_of,
                                 skip_tags=skip_tags, lang=lang)
        yielded = 0
        try:
            stream = stream_chat(prov_name, model_i, messages, api_key=key_i,
                                 ollama_url=cfg.get("ollama_url", ""),
                                 temperature=float(cfg.get("temperature", 0.3)),
                                 images=images)
            for ev in stream:
                yielded += 1
                for kind, text in splitter.feed(ev["type"], ev["text"]):
                    if not text:
                        continue
                    acc["thinking" if kind == "thinking" else "content"] += text
                    yield {"type": kind, "delta": text}
            for kind, text in splitter.flush():
                if not text:
                    continue
                acc["thinking" if kind == "thinking" else "content"] += text
                yield {"type": kind, "delta": text}
            return
        except LLMError as e:
            last_err = e
            if yielded:
                # فشل في منتصف البث — إعادة المحاولة ستكرر النص؛ ارفع الخطأ كما هو
                yield {"type": "error", "text": str(e)}
                raise
            yield {"type": "fallback", "text": str(e)}
            continue
    if last_err:
        raise last_err


def _offline_answer(query: str, sources: list[dict], lang: str = "ar") -> Generator[dict, None, None]:
    """وضع محلي بدون LLM: يعرض أقرب ما في الفهرس + نصائح تفعيل النموذج (عربي/إنجليزي)."""
    hits = rag.search(query, k=4, min_score=0.01)
    en = lang == "en"
    if en:
        yield {"type": "content", "delta": "### 📡 Local Mode (no LLM configured)\n\n"}
        yield {"type": "content", "delta": ("I'm running **without an LLM** right now — showing the closest matches from the "
                                            "knowledge base and your indexed files. Tools (GPA/CV) work fully.\n\n")}
        if hits:
            yield {"type": "content", "delta": "#### Closest matches:\n\n"}
            for i, h in enumerate(hits, 1):
                excerpt = h["text"][:400].replace("\n", " ")
                yield {"type": "content", "delta": f"**{i}. {h['title']}** (source: {h['source']})\n> {excerpt}…\n\n"}
        else:
            yield {"type": "content", "delta": "No matching chunks found — rephrase, add files, then press “Re-index”.\n\n"}
        yield {"type": "content", "delta": (
            "#### To enable full AI intelligence (100% free):\n"
            "1. **Best & fully offline:** install [Ollama](https://ollama.com) then run `ollama pull llama3.1:8b`\n"
            "2. **Or add a free key** from [Groq](https://console.groq.com), [OpenRouter](https://openrouter.ai/keys) or [Gemini](https://aistudio.google.com) in ⚙️ Settings\n\n"
            "Ready now: the 🧮 GPA calculator and 💼 CV builder buttons.")}
        return
    yield {"type": "content", "delta": "### 📡 الوضع المحلي (بدون نموذج لغوي)\n\n"}
    yield {"type": "content", "delta": ("أنا شغّال الآن **بدون LLM** — بجيب لك أقرب ما في قاعدة المعرفة "
                                        "وملفاتك المفهرسة، والأدوات (GPA/CV) بتشتغل كاملة.\n\n")}
    if hits:
        yield {"type": "content", "delta": "#### أقرب المقاطع للموضوع:\n\n"}
        for i, h in enumerate(hits, 1):
            excerpt = h["text"][:400].replace("\n", " ")
            yield {"type": "content", "delta": f"**{i}. {h['title']}** (المصدر: {h['source']})\n> {excerpt}…\n\n"}
    else:
        yield {"type": "content", "delta": "لم أجد مقاطع مطابقة في الفهرس — جرّب صياغة أخرى أو أضف ملفاتك ثم اضغط «تحديث الفهرس».\n\n"}
    yield {"type": "content", "delta": (
        "#### لتشغيل الذكاء الكامل (مجاني 100%):\n"
        "1. **الأفضل والأسرع بدون إنترنت:** ثبّت [Ollama](https://ollama.com) ثم نفّذ `ollama pull llama3.1:8b`\n"
        "2. **أو أدخل مفتاح مجاني** من [Groq](https://console.groq.com) أو [OpenRouter](https://openrouter.ai/keys) أو [Gemini](https://aistudio.google.com) في ⚙️ الإعدادات\n\n"
        "أدوات جاهزة الآن: زر 🧮 لحساب GPA وزر 💼 لبناء CV.")}


def run_stream(*, chat_id: str, message: str, attachments: list[dict] | None = None,
               agent_hint: str | None = None, regenerate: bool = False,
               lang: str = "ar") -> Generator[str, None, None]:
    """النقطة الرئيسية — يرجع أسطر SSE (data: {json})."""
    cfg = load_config()
    prov = resolve_provider(cfg)
    attachments = attachments or []

    def sse(obj: dict) -> str:
        return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"

    # ---------- تجميع مرفقات
    att_notes: list[str] = []
    images: list[str] = []
    for a in attachments:
        name = a.get("name") or "مرفق"
        text = (a.get("text") or "").strip()
        if text:
            att_notes.append(f"[مرفق: {name}]\n{text[:8000]}")
        else:
            att_notes.append(f"[مرفق: {name}] — ملف وسائط؛ حاول تحليله من محتواه إن أمكن.")
        data_url = a.get("dataUrl")
        if not data_url and a.get("library_id"):
            try:
                from core import history as _h
                item = _h.get_library_item(str(a.get("library_id")))
                if item:
                    from pathlib import Path as _P
                    up = _P(__file__).resolve().parents[1] / "uploads" / str(item.get("stored_name",""))
                    mime = (item.get("mime") or "").lower()
                    if up.is_file() and mime.startswith("image/"):
                        import base64
                        b = up.read_bytes()
                        if len(b) <= 6 * 1024 * 1024:
                            data_url = "data:" + mime + ";base64," + base64.b64encode(b).decode("ascii")
            except Exception:
                pass
        if data_url and str(data_url).startswith("data:image/"):
            images.append(data_url)

    # ---------- تاريخ المحادثة (نجلب آخر 8 رسائل ما عدا الأخيرة المكررة عند التوليد)
    from core import history as hist
    msgs = hist.get_messages(chat_id)
    if regenerate and not message:
        for m in reversed(msgs):
            if m["role"] == "user":
                message = m["content"]
                break
        user_idx = next((i for i in range(len(msgs) - 1, -1, -1) if msgs[i]["role"] == "user"), None)
        history_msgs = msgs[:user_idx] if user_idx is not None else []
    else:
        history_msgs = msgs[:-1]

    tail = [{"role": m["role"], "content": m["content"]} for m in history_msgs][-8:]

    # ---------- استعادة رسالة إعادة التوليد + فلتر الرؤية
    if not message:
        message = "أعد صياغة إجابتك السابقة بشكل أفضل وبدقة أعلى."
    route_extra = ""  # ملاحظات نظام تُضاف لسياق الوكيل (تُعرَّف مبكراً لتجنب UnboundLocalError)
    vision_unsupported = False
    if images:
        # التوجيه الذكي للرؤية: بدل حذف الصور، بدّل تلقائياً لأول مزود/نموذج قادر على الرؤية
        # (المزود الحالي إن كان يدعمها → Gemini → نموذج رؤية مجاني على OpenRouter بمفتاحه الخاص).
        if not provider_supports_vision(prov["provider"], prov.get("model", "")):
            vision_prov = None
            gem_key = (cfg.get("api_keys") or {}).get("gemini", "")
            if gem_key:
                vision_prov = ("gemini", (cfg.get("main_models") or {}).get("gemini") or "gemini-flash-lite-latest", gem_key)
            else:
                for alt in ("google/gemma-4-26b-a4b-it:free", "google/gemma-4-31b-it:free", "meta-llama/llama-4-scout:free"):
                    k = get_model_key("openrouter", alt, cfg)
                    if k and provider_supports_vision("openrouter", alt):
                        vision_prov = ("openrouter", alt, k)
                        break
            if vision_prov:
                prov = {**prov, "provider": vision_prov[0], "model": vision_prov[1], "vision_model": vision_prov[1]}
                yield sse({"type": "notice", "text": (f"🖼️ تم التبديل التلقائي إلى {vision_prov[0]} ({vision_prov[1]}) لتحليل الصور"
                                                      if lang == "ar" else f"🖼️ Switched to {vision_prov[0]} ({vision_prov[1]}) for image analysis")})
            else:
                vision_unsupported = True
                route_extra += ("\n\n[System: User attached image(s), but no vision-capable provider is configured. "
                                "Do NOT claim you saw the image. Ask the user to add a Gemini key in Settings, or describe what is needed. Be explicit and honest.]")
                images = []
        else:
            prov = {**prov, "vision_model": prov.get("model", "")}
        if images:
            route_extra += ("\n\n[System: The user attached image(s) which are provided to you as real visual input. "
                            "Analyze what you actually SEE in them (objects, people, text/OCR, colors, layout, charts, diagrams). "
                            "Be concrete and specific; distinguish what is clearly visible from what is uncertain. Never say you cannot see the image.]")

    # ---------- نوايا حتمية
    # ---------- Greeting / smalltalk fast path
    clean_msg = (message or "").strip()
    if 'GREETING_RE' in globals() and GREETING_RE.match(clean_msg) and not attachments and not images:
        yield sse({"type": "route", "agents": [{"id": "research", "name": AGENT_MAP["research"]["name"], "icon": AGENT_MAP["research"].get("icon","🔍")}]})
        greet = "أهلًا! كيف أقدر أساعدك اليوم؟" if lang == "ar" else "Hi! How can I help you today?"
        yield sse({"type": "content", "delta": greet})
        yield sse({"type": "done", "content": greet, "thinking": "", "sources": []})
        return
    if 'SHORT_SMALLTALK_RE' in globals() and SHORT_SMALLTALK_RE.match(clean_msg) and not attachments and not images:
        yield sse({"type": "route", "agents": [{"id": "research", "name": AGENT_MAP["research"]["name"], "icon": AGENT_MAP["research"].get("icon","🔍")}]})
        reply = "على الرحب والسعة! إذا احتجت أي مساعدة أنا موجود." if lang == "ar" else "You're welcome! I'm here if you need anything."
        yield sse({"type": "content", "delta": reply})
        yield sse({"type": "done", "content": reply, "thinking": "", "sources": []})
        return

    tool_markdown = ""
    suggest: list[str] = []
    gpa_intent = bool(GPA_RE.search(message))
    cv_intent = bool(CV_RE.search(message))
    if gpa_intent:
        rows = parse_gpa_rows(message)
        if rows:
            try:
                has_letter_grades = any(re.match(r"^[A-F][+-]?$", str(r.get("grade", "")).strip(), re.I) for r in rows)
                scale = "standard4" if has_letter_grades else "egypt5"
                res = gpatool.calc(rows, scale=scale, lang=lang)
                tool_markdown = gpatool.to_markdown(res, lang=lang)
                route_extra += "\n\nنتيجة حاسبة GPA المحلية (احتسبها وأعدها للطالب مؤكدة): \n" + tool_markdown
            except Exception:
                pass
        suggest.append("gpa")
    if cv_intent:
        suggest.append("cv")

    # ---------- التوجيه (كلمات مفتاحية واثقة أولاً = أسرع، وإلا LLM)
    route = None
    if _keywords_confident(message):
        route = _classify_keywords(message)
    if route is None and prov["provider"] != "offline":
        route = _classify_llm(message, cfg, prov)
    if route is None:
        route = _classify_keywords(message)
    if agent_hint and agent_hint in AGENT_MAP:
        route["agents"] = [agent_hint] + [a for a in route["agents"] if a != agent_hint]
    if cv_intent and "career" not in route["agents"]:
        route["agents"] = ["career"] + route["agents"][: cfg.get("max_agents", 2) - 1]
    route["agents"] = route["agents"][: max(1, int(cfg.get("max_agents", 2)))]

    # ---------- RAG + ويب (استرجاع ثنائي اللغة: سؤال إنجليزي يبحث عربي والعكس)
    ctx_block, sources = "", []
    if route.get("needs_rag", True):
        search_query = message
        try:
            has_ar = bool(re.search(r"[\u0600-\u06FF]", message))
            has_en = bool(re.search(r"[A-Za-z]", message))
            alt = None
            if has_en and not has_ar:
                alt = quick_translate(message, "ar")
            elif has_ar and not has_en:
                alt = quick_translate(message, "en")
            if alt:
                search_query = message + "\n" + alt
        except Exception:
            pass
        try:
            ctx_block, sources = rag.build_context(search_query, k=int(cfg.get("rag_k", 6)))
        except Exception:
            ctx_block, sources = "", []
    web_sources: list[dict] = []
    web_block = ""
    if route.get("needs_web") and cfg.get("web_search", True):
        try:
            results = websearch.web_search_all(message, lang=lang, n=5)
            if results:
                lines = ["=== نتائج بحث إنترنت حديثة (اذكر المصدر برابطه عند الاعتماد عليها) ==="]
                for i, w in enumerate(results, 1):
                    lines.append(f"[W{i}] {w['title']}\n{w['url']}\n{w.get('snippet', '')[:300]}")
                    web_sources.append({"title": w["title"], "source": "ويب", "url": w["url"], "kind": "web"})
                web_block = "\n\n".join(lines)
        except Exception:
            pass

    # ---------- بناء رسالة المستخدم الموسعة
    parts = [f"سؤال المستخدم:\n{message}"]
    if att_notes:
        parts.append("=== مرفقات المستخدم ===\n" + "\n\n".join(att_notes))
    if ctx_block:
        parts.append(ctx_block)
    if web_block:
        parts.append(web_block)
    user_block = "\n\n".join(parts)

    yield sse({"type": "route", "agents": [{"id": a, "emoji": AGENT_MAP[a]["emoji"], "name": AGENT_MAP[a]["name"]}
                                           for a in route["agents"]],
               "complexity": route["complexity"], "offline": prov["provider"] == "offline"})
    if suggest:
        yield sse({"type": "suggest_tool", "tools": suggest})
    if tool_markdown:
        yield sse({"type": "tool", "tool": "gpa", "markdown": tool_markdown})

    all_think, all_content = "", ""
    try:
        if prov["provider"] == "offline":
            for ev in _offline_answer(message, sources, lang):
                all_content += ev.get("delta", "")
                yield sse(ev)
        else:
            primary = route["agents"][0]
            acc = {"thinking": "", "content": ""}
            for ev in _stream_agent(primary, cfg, prov, user_block, tail,
                                    extra_context=route_extra, images=images or None, acc=acc,
                                    lang=lang):
                yield sse(ev)
            all_think, all_content = acc["thinking"], acc["content"]
            if len(route["agents"]) > 1 and all_content.strip():
                second = route["agents"][1]
                yield sse({"type": "agent_switch", "agent": {"id": second, "emoji": AGENT_MAP[second]["emoji"],
                                                              "name": AGENT_MAP[second]["name"]}})
                yield sse({"type": "content", "delta": "\n\n"})
                acc2 = {"thinking": "", "content": ""}
                sec_extra = (route_extra + "\n\n" if route_extra else "") + f"إجابة الزميل الأول:\n{all_content[:3500]}"
                for ev in _stream_agent(second, cfg, prov, user_block, tail,
                                        extra_context=sec_extra,
                                        secondary_of=primary, images=images or None, acc=acc2, lang=lang):
                    yield sse(ev)
                if acc2["thinking"]:
                    all_think += ("\n\n" + acc2["thinking"])
                if acc2["content"]:
                    all_content += ("\n\n" + acc2["content"])
    except LLMError as e:
        yield sse({"type": "error", "text": str(e)})
        # هبوط آمن: أجب من الفهرس فقط لو لم يُبث أي محتوى
        if not all_content.strip():
            for ev in _offline_answer(message, sources, lang):
                all_content += ev.get("delta", "")
                yield sse(ev)

    final_sources = sources + web_sources
    yield sse({"type": "sources", "sources": final_sources})
    yield sse({"type": "done", "thinking": all_think, "content": all_content, "sources": final_sources})
