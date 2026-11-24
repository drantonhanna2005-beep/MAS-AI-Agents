"""إعدادات النظام — تحميل/حفظ config.json وكشف المزود المتاح تلقائياً.

المزودات المدعومة (كلها مجانية):
- ollama      : تشغيل محلي 100% بدون أي API key (الأفضل للخصوصية والسرعة)
- groq        : طبقة مجانية سريعة جداً (مفتاح من console.groq.com)
- openrouter  : نماذج مجانية بلاحقة :free (مفتاح من openrouter.ai)
- gemini      : طبقة Google AI Studio المجانية (مفتاح من aistudio.google.com)
- offline     : بدون أي LLM — يجيب من قاعدة المعرفة والملفات المفهرسة + الأدوات الحتمية
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]      # university-ai-agents/
DATA_DIR = ROOT / "data"                        # ملفات الطالب للتدريب (الدرويفات تُنزل هنا)
UPLOAD_DIR = ROOT / "uploads"                   # مرفقات الشات
INDEX_DIR = ROOT / "index_store"                # فهرس RAG
CONFIG_PATH = ROOT / "config.json"
DB_PATH = ROOT / "history.db"

for _d in (DATA_DIR, UPLOAD_DIR, INDEX_DIR):
    _d.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG: dict = {
    "provider": "auto",           # auto | ollama | groq | openrouter | gemini | offline
    "api_keys": {"groq": "", "openrouter": "", "gemini": ""},
    "main_models": {
        "ollama": "llama3.1:8b",
        "groq": "openai/gpt-oss-20b",
        "openrouter": "openrouter/free",
        "gemini": "gemini-2.0-flash",
    },
    "router_models": {
        "ollama": "llama3.2:3b",
        "groq": "llama-3.1-8b-instant",
        "openrouter": "openrouter/free",
        "gemini": "gemini-2.0-flash",
    },
    "model_keys": {"openrouter": {}},   # مفتاح خاص لكل نموذج (لو المفاتيح من حسابات مختلفة)
    "stt": {"model": "whisper-large-v3-turbo"},                                   # تحويل صوت → نص (Groq Whisper)
    "tts": {"model": "heygen/heygen-voice-1-turbo:free", "voice": "nadine"},      # نص → صوت حقيقي (OpenRouter)
    "embed": {"provider": "auto", "model": "nvidia/nemotron-3-embed-1b:free"},   # بحث دلالي مجاني بدون Ollama
    "ollama_url": "http://localhost:11434",
    "temperature": 0.3,
    "deep_think": True,           # عرض "تفكير عميق" قبل الإجابة
    "web_search": True,           # السماح بالبحث في الإنترنت
    "rag_k": 6,                   # عدد المقاطع المسترجعة لكل سؤال
    "embed_model": "nomic-embed-text",
    "max_agents": 2,              # أقصى عدد وكلاء يشاركون في إجابة واحدة
}


def get_model_key(provider: str, model: str, cfg: dict) -> str:
    """مفتاح النموذج: مفتاح خاص بالنموذج (model_keys) إن وجد وإلا مفتاح المزود."""
    mk = (cfg.get("model_keys") or {}).get(provider) or {}
    return (mk.get(model) or cfg.get("api_keys", {}).get(provider, "")).strip()


def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_PATH.exists():
        try:
            user = json.loads(CONFIG_PATH.read_text("utf-8"))
            for k, v in user.items():
                if v is not None:
                    cfg[k] = v
            if isinstance(user.get("api_keys"), dict):
                cfg["api_keys"].update({k: v for k, v in user["api_keys"].items() if v})
        except Exception:
            pass  # ملف تالف → نرجع للإعدادات الافتراضية
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")


def _ollama_models(url: str) -> list[str] | None:
    """يرجع قائمة موديلات Ollama لو الخادم شغال، وإلا None."""
    try:
        import httpx
        r = httpx.get(url.rstrip("/") + "/api/tags", timeout=1.5)
        if r.status_code == 200:
            return [m.get("name", "") for m in r.json().get("models", [])]
    except Exception:
        pass
    return None


def pick_ollama_model(models: list[str], wanted: str) -> str:
    """يختار أفضل موديل متاح: المطلوب إن وجد، وإلا أقرب موديل مناسب."""
    if not models:
        return wanted or ""
    if wanted and any(m == wanted or m.startswith(wanted + ":") for m in models):
        return next(m for m in models if m == wanted or m.startswith(wanted + ":"))
    for pref in ("llama3.1", "llama3.2", "qwen2.5", "mistral", "gemma", "llama3", "phi"):
        hit = [m for m in models if pref in m.lower()]
        if hit:
            return sorted(hit)[-1]
    return models[0]


def resolve_provider(cfg: dict) -> dict:
    """يحدد المزود الفعلي المستخدم حسب الإعدادات والتوفر اللحظي."""
    want = (cfg.get("provider") or "auto").lower()
    keys = cfg.get("api_keys", {})
    ollama_url = cfg.get("ollama_url", DEFAULT_CONFIG["ollama_url"])
    ollama_models = _ollama_models(ollama_url) or []
    ollama_up = bool(ollama_models)

    order = [want] if want != "auto" else ["ollama", "groq", "openrouter", "gemini"]
    for p in order:
        if p == "ollama" and ollama_up:
            model = pick_ollama_model(ollama_models, cfg["main_models"].get("ollama", ""))
            return {"provider": "ollama", "model": model, "available_models": ollama_models,
                    "ollama_url": ollama_url}
        if p == "groq" and keys.get("groq"):
            return {"provider": "groq", "model": cfg["main_models"]["groq"], "available_models": []}
        if p == "openrouter" and keys.get("openrouter"):
            return {"provider": "openrouter", "model": cfg["main_models"]["openrouter"], "available_models": []}
        if p == "gemini" and keys.get("gemini"):
            return {"provider": "gemini", "model": cfg["main_models"]["gemini"], "available_models": []}

    return {"provider": "offline", "model": "—", "available_models": ollama_models,
            "ollama_up": ollama_up, "ollama_url": ollama_url}


def provider_supports_vision(provider: str, model: str) -> bool:
    m = (model or "").lower()
    if provider == "gemini":
        return True
    if provider == "ollama":
        return any(k in m for k in ("llava", "vision", "bakllava", "moondream", "minicpm-v", "llama3.2-vision", "gemma3", "qwen2.5vl", "qwen-vl", "phi3.5-vision", "phi4-multimodal"))
    # broad heuristic for OpenAI-compatible providers; allow common vision-capable families
    if any(k in m for k in ("gpt-4o", "gpt-4.1", "gpt-4-turbo", "gpt-5", "omni", "vision", "4v", "claude-3", "claude-sonnet-4", "claude-opus-4", "claude-haiku-4", "llama-3.2-vision", "llama-4", "scout", "maverick", "pixtral", "qwen-vl", "qwen2.5-vl", "qwen2-vl", "gemini", "gemma-3", "internvl", "minicpm-v", "moondream")):
        return True
    if provider in ("openai", "azure", "openrouter", "groq", "together", "fireworks", "deepinfra", "mistral"):
        # conservative default false for unknown text-only models on these providers
        return False
    return False
