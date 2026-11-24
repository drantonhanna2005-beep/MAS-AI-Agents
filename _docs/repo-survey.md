# مسح مستودع awesome-llm-apps: أنماط قابلة لإعادة الاستخدام لنظام Multi-Agent أكاديمي

**تاريخ المسح:** 2026-10-27
**النطاق:** المستودع المحلي في جذر مساحة العمل (فرع العمل الحالي)، قراءة فقط.
**السؤال المطروح:** ما الأنماط الهندسية الفعلية (لا المفترضة) في هذا المستودع التي تصلح لبناء نظام وكلاء أكاديمي بواجهة شات ويب + RAG محلي بدون API مدفوع؟

**منهجية:** فحصت شجرة المجلدات، ثم ثبّتت خمسة تطبيقات مرشحة بحسب الفئة المطلوبة، وقرأت ملفاتها الرئيسية سطراً بسطر مع ملفات `requirements.txt`. كل ادعاء أدناه مسنود إلى `مسار:سطر` أو إلى محتوى ملف اعتماديات. لم أشغّل أي تطبيق؛ الاستنتاجات عن السلوك مبنية على قراءة الكود لا على تنفيذ.

---

## 1. الخلاصة التنفيذية

الأنماط القابلة لإعادة الاستخدام موجودة، لكنها **ليست** في طبقة "تنسيق الوكلاء" كما يوحي اسم المستودع؛ هي في ثلاث طبقات أدنى:

1. **طبقة تجميع السياق (Context Assembly)** — كل تطبيقات RAG هنا تُمرّر المعرفة إلى النموذج كنص واحد مُجمَّع يدوياً أو كـ callback بحث. لا يوجد "وكيل RAG" حقيقي إلا في `local_rag_agent`.
2. **طبقة التوجيه الحتمي (Deterministic Routing)** — التوجيه الفعلي في الكود إما تسلسل يدوي، أو JSON يصدره وكيل triage ويقرأه Python، أو `Team(mode="coordinate")` من agno.
3. **طبقة الحالة (State)** — السجل إما `st.session_state` (يضيع مع إعادة التشغيل)، أو SQLite، أو ذاكرة mem0 في Qdrant.

الاكتشاف الأهم: **فريق التعليم المطلوب لا يمرّر مخرجات وكيل إلى وكيل**. الأربعة يتلقون نفس الموضوع نصياً، والتنسيق شكلي في واجهة Streamlit. أي نظام أكاديمي جاد يجب أن يبني سلسلة تمرير سياق حقيقية، لأن المستودع لا يقدمها جاهزة في هذا التطبيق.

---

## 2. القائمة المختصرة: أفضل 5 تطبيقات

| # | الفئة المطلوبة | المجلد | الإطار | يحتاج API مدفوع؟ |
|---|---|---|---|---|
| 1 | فريق وكلاء تعليمي | `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/` | agno + Streamlit | نعم (OpenAI + Composio + SerpAPI) |
| 2 | RAG محلي بلا مفاتيح | `rag_tutorials/local_rag_agent/` | agno (AgentOS) | لا |
| 3 | شات بذاكرة/سجل محلي | `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/` | لا شيء (mem0 + litellm) | لا (Ollama محلي) |
| 4 | وكيل صوتي | `voice_ai_agents/voice_rag_openaisdk/` | OpenAI Agents SDK | نعم (LLM + TTS) |
| 5 | Hybrid Search RAG | `rag_tutorials/local_hybrid_search_rag/` | لا شيء (RAGLite) | لا (GGUF محلي) |

**إضافة عالية الصلة (خارج الخمسة لكن الأقرب لهدفك):** `advanced_ai_agents/multi_agent_apps/agent_teams/ai_legal_agent_team/local_ai_legal_agent_team/` — فريق multi-agent **محلي بالكامل** (Ollama + Qdrant + agno Team + Knowledge مشتركة). هذا هو التطبيق الوحيد في المستودع الذي يجمع الثلاثة معاً: فريق وكلاء + RAG محلي + بلا مفاتيح.

---

## 3. تفصيل التطبيقات الخمسة

### 3.1 فريق الوكلاء التعليمي — `ai_teaching_agent_team`

**المسار:** `advanced_ai_agents/multi_agent_apps/agent_teams/ai_teaching_agent_team/`
**الملفات:** `teaching_agent_team.py` (ملف واحد، ~200 سطر)، `README.md`، `requirements.txt`
**الإطار:** agno (`agno>=2.2.10`) + Streamlit. لا يُستخدم `agno.team.Team` إطلاقاً — التنسيق مكتوب يدوياً.

**الوكلاء الأربعة** (كلهم `OpenAIChat(id="gpt-4o-mini")`):

| الوكيل | الدور المعلن | الأدوات | السطر |
|---|---|---|---|
| Professor | Research and Knowledge Specialist | `google_docs_tool` | 51 |
| Academic Advisor | Learning Path Designer | `google_docs_tool` | 67 |
| Research Librarian | Learning Resource Specialist | `google_docs_tool` + `SerpApiTools` | 85 |
| Teaching Assistant | Exercise Creator | `google_docs_tool` + `SerpApiTools` | 102 |

**كيف يُعرَّف الوكيل:** نمط agno التصريحي — `Agent(name=..., role=..., model=..., tools=[...], instructions=[...], debug_mode=True, markdown=True)`. التعليمات هي كل "منطق" الوكيل؛ لا callbacks ولا schemas مخرجات.

**كيف يُمرَّر السياق (الاكتشاف الحرج):** التسلسل في `teaching_agent_team.py:136-151`:

```python
professor_response = professor_agent.run(f"the topic is: {topic},Don't forget to add the Google Doc link...")
academic_advisor_response = academic_advisor_agent.run(f"the topic is: {topic},...")
research_librarian_response = research_librarian_agent.run(f"the topic is: {topic},...")
teaching_assistant_response = teaching_assistant_agent.run(f"the topic is: {topic},...")
```

كل وكيل يستلم **نفس نص الموضوع فقط**. مخرجات Professor لا تُمرَّر إلى Academic Advisor رغم أن تعليمات الأخير تقول "Using the knowledge base for the given topic". التجميع يحدث في الواجهة فقط عبر `pprint_run_response`. أي: **fan-out متساوٍ بلا تمرير سياق بيني**، والتنسيق تجميلي.

**ملاحظة أدوات:** `ArxivTools` مستورد في السطر 9 وغير مستخدم في أي وكيل. `ComposioToolSet` يحتاج مفتاح Composio حتى لو أردت تعطيل Google Docs.

**المفاتيح المطلوبة:** OpenAI + Composio + SerpAPI (الشريط الجانبي، سطور 28-32).

---

### 3.2 RAG محلي بدون مفاتيح — `local_rag_agent`

**المسار:** `rag_tutorials/local_rag_agent/`
**الملفات:** `local_rag_agent.py` (~28 سطراً)، `README.md`، `requirements.txt`
**الإطار:** agno — `Agent` + `Knowledge` + `AgentOS`.
**الاعتماديات:** `agno>=2.2.10`, `qdrant-client`, `ollama`, `pypdf`. **لا مفاتيح API.**

**البنية (كلها في ملف واحد):**

```python
vector_db = Qdrant(collection="thai-recipe-index", url="http://localhost:6333/", embedder=OllamaEmbedder())
knowledge_base = Knowledge(vector_db=vector_db)
knowledge_base.add_content(url="https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf")
agent = Agent(name="Local RAG Agent", model=Ollama(id="llama3.2"), knowledge=knowledge_base)
agent_os = AgentOS(agents=[agent]); app = agent_os.get_app()
```

**نقاط معمارية:**
- الفهرسة تتم عند الاستيراد (`add_content` في المستوى الأعلى للملف) — ليست خاملة ولا idempotente؛ إعادة التشغيل تعيد الفهرسة.
- التضمين محلي عبر `OllamaEmbedder`، والنموذج `llama3.2` عبر Ollama.
- الواجهة **ليست Streamlit**: `AgentOS.serve()` يولد واجهة ويب + API من تعريف الوكيل. هذا أخف مسار "شات ويب" في المستودع كله (لا كود UI إطلاقاً).
- لا يوجد في الكود أي تخصيص لعدد القطع المسترجعة أو للـ prompt؛ agno يتولى حلقة "ابحث ثم أجب" داخلياً.

**الاستخدام العملي:** هذا هو القالب الأدنى لـ RAG محلي. انسخه ثم استبدل PDF بفهرس مواد أكاديمية، و`AgentOS` بواجهة شات مخصصة إن احتجت تحكماً.

---

### 3.3 شات بذاكرة/سجل محلي — `local_chatgpt_with_memory`

**المسار:** `advanced_llm_apps/llm_apps_with_memory_tutorials/local_chatgpt_with_memory/`
**الملفات:** `local_chatgpt_memory.py` (~130 سطراً)، `README.md`، `requirements.txt`
**الإطار:** **لا شيء** — `mem0ai==0.1.29` + `litellm` + `streamlit` مباشرة.

**تكوين الذاكرة (سطور 5-27):** Qdrant على `localhost:6333` (collection `local-chatgpt-memory`، أبعاد 768) + LLM `ollama/llama3.1:latest` + embedder `nomic-embed-text:latest` على `localhost:11434`.

**تدفق الرسالة الواحدة:**
1. `st.session_state.messages.append(user)` — للسجل المعروض.
2. `m.add(prompt, user_id=user_id)` — كتابة في الذاكرة الدائمة.
3. `m.get_all(user_id=user_id)` ثم بناء `context` كنص بنقاط.
4. استدعاء واحد: `completion(model="ollama/llama3.1:latest", messages=[system, user(f"Context...{context}\nCurrent message: {prompt}")], api_base="http://localhost:11434", stream=True)`.
5. `m.add(f"Assistant: {full_response}")`.

**اكتشاف مهم:** قائمة `st.session_state.messages` **لا تُرسل إلى النموذج**. النموذج يرى رسالة نظام + رسالة مستخدم واحدة تحمل ملخص الذاكرة والسؤال الحالي. أي أن "تاريخ المحادثة" هنا للعرض فقط، والاستمرارية تأتي حصراً من mem0 (استرجاع دلالي، لا سجل خام). هذا يفسّر لماذا لا تنفجر التكلفة/الطول، لكنه يفقد الدقة الحرفية للسياق القريب.

**بديل أدنى (مرجعي):** `llm_apps_with_memory_tutorials/llama3_stateful_chat/local_llama3_chat.py` — 40 سطراً، `streamlit` + `openai` فقط، يوجّه العميل إلى LM Studio على `localhost:1234/v1`، ويرسل **كل** `st.session_state.messages` في كل طلب. لا ذاكرة دلالية، لكنه أبسط نموذج "سجل محلي" في المستودع.

---

### 3.4 وكيل صوتي — `voice_rag_openaisdk`

**المسار:** `voice_ai_agents/voice_rag_openaisdk/`
**الملفات:** `rag_voice.py` (~330 سطراً)، `README.md`، `requirements.txt`
**الإطار:** OpenAI Agents SDK (`openai-agents==0.4.2`) + Streamlit + `fastembed` + `qdrant-client` + LangChain splitters/loaders.

**التضمين محلي:** `TextEmbedding()` من fastembed، والأبعاد تُكتشف عملياً بتضمين كلمة "test" ثم `len(...)` (سطور 86-90) — نمط ذكي لتفادي تثبيت البعد يدوياً.

**وكيلان** (كلاهما `gpt-4o`، سطور 147-172):
- `processor_agent` — "Documentation Processor": يجيب من السياق ويذكر المصادر.
- `tts_agent` — "Text-to-Speech Agent": يحوّل الجواب إلى **تعليمات أداء صوتي** (إيقاع، تشديد، وقفات).

**خط الأنابيب (دالة `process_query`، 6 خطوات معلنة):**
1. تضمين السؤال → `client.query_points(limit=3)`.
2. بناء نص سياق يدوياً: `"Based on the following documentation:\n\nFrom {source}:\n{content}"`.
3. `Runner.run(processor_agent, context)` → نص الجواب.
4. `Runner.run(tts_agent, text_response)` → تعليمات الصوت.
5. `AsyncOpenAI.audio.speech.with_streaming_response.create(model="gpt-4o-mini-tts", voice=..., response_format="pcm", instructions=voice_instructions)` → `LocalAudioPlayer().play(...)`.
6. إنشاء MP3 للتنزيل.

**قيود يجب معرفتها:** يحتاج مفتاح OpenAI (LLM + TTS)، ويطلب `qdrant_url` + `qdrant_api_key` معاً — أي أن Qdrant المحلي يحتاج مفتاحاً وهمياً. الإطار هنا **زخرفة تنظيمية**: لا tools ولا handoffs؛ الوكيلان غلافان حول prompt، والسياق نص مُجمَّع يدوياً. لا يوجد STT (إدخال صوتي) في هذا التطبيق — الإدخال نصي والمخرجات صوتية فقط.

---

### 3.5 Hybrid Search RAG — `local_hybrid_search_rag`

**المسار:** `rag_tutorials/local_hybrid_search_rag/`
**الملفات:** `local_main.py` (~250 سطراً)، `README.md`، `requirements.txt`
**الإطار:** **لا شيء** — `raglite==0.2.1` + `llama-cpp-python` + `rerankers==0.6.0` + `flashrank` + Streamlit.

**التكوين:** `RAGLiteConfig(db_url=..., llm="llama-cpp-python/<GGUF>", embedder="llama-cpp-python/<GGUF>", embedder_normalize=True, chunk_max_size=512, reranker=Reranker("ms-marco-MiniLM-L-12-v2", model_type="flashrank"))` — النموذجان محليان بصيغة GGUF، والـ reranker محلي أيضاً.

**خط الأنابيب الفعلي:**
```python
chunk_ids, scores = hybrid_search(query, num_results=10, config=...)
chunks = retrieve_chunks(chunk_ids, config=...)
reranked = rerank_chunks(query, chunks, config=...)      # إعادة ترتيب
stream = rag(prompt=query, system_prompt=RAG_SYSTEM_PROMPT,
             search=hybrid_search, messages=formatted_messages,
             max_contexts=5, config=...)                  # توليد
```

**أنماط جديرة بالنسخ:**
- **fallback صريح:** إذا أعاد البحث صفر قطع → `rag(..., search=None)` إجابة من المعرفة العامة مع إشعار المستخدم (سطور 224-232). لا انهيار صامت.
- **السجل يُعاد تشكيله** من أزواج `(user, assistant)` إلى `messages` متناوبة قبل كل طلب — أي أن هذا التطبيق (بخلاف 3.3) يمرّر التاريخ فعلياً.
- **بث مع مؤشر:** `message_placeholder.markdown(full_response + "▌")`.
- **قاعدة البيانات:** الواجهة تطلب `postgresql://...` و`psycopg2-binary` موجود في المتطلبات؛ RAGLite نفسه يدعم SQLite، لكن الكود المعروض يفترض Postgres. هذه نقطة احتكاك لتشغيل محلي خفيف.

**مقارنة مباشرة:** `rag_tutorials/hybrid_search_rag/` هو نفس خط الأنابيب لكن بمفاتيح OpenAI + Anthropic + Cohere (Claude 3 Opus + text-embedding-3-large + Cohere rerank). النسخة المحلية هي البديل المطابق وظيفياً بلا تكلفة.

---

## 4. أنماط التوجيه والتعاون الموجودة فعلاً في الكود

هذه أنماط مقروءة من الملفات، لا استنتاجات تصميمية.

### النمط A — تسلسل يدوي بلا تمرير سياق (fan-out متساوٍ)
**الدليل:** `ai_teaching_agent_team/teaching_agent_team.py:136-151`.
**الوصف:** كود الواجهة يستدعي `agent.run()` أربع مرات متتالية، كل مرة بنفس المُدخل. لا `Team`، لا رسائل بين الوكلاء، لا تجميع آلي. التعاون "موجود" في النص التسويقي فقط.
**مناسب لـ:** مهام يمكن تقسيمها على نفس المُدخل (توليد أربع وثائق مستقلة). **غير مناسب** لبناء مسار تعليمي متكامل يعتمد فيه كل وكيل على سابق.

### النمط B — تفويض عبر `agno.Team` (coordinate)
**الأدلة:**
- `ai_travel_planner_agent_team/backend/agents/team.py:22-31`: `Team(name="TripCraft AI Team", mode="coordinate", model=model, tools=[ReasoningTools(...)], members=[destination, hotel_search, dining, budget, flight_search, itinerary])` + `description` + `instructions` طويلة تصف دور المنسّق.
- `ai_finance_agent_team/finance_agent_team.py:10-38`: `SqliteDb(db_file="agents.db")` مشتركة، `add_history_to_context=True` على كل عضو، ثم `Team(members=[web_agent, finance_agent])` بلا `mode` صريح (الافتراضي)، وتقديم عبر `AgentOS(teams=[agent_team])`.
- `ai_legal_agent_team/local_ai_legal_agent_team/local_legal_agent.py:120-135`: `Team(name="Legal Team Lead", model=Ollama("llama3.1:8b"), members=[...3 وكلاء Ollama...], knowledge=kb, search_knowledge=True)`.

**الوصف:** النموذج يعمل كمنسّق؛ agno يحقن أوصاف الأعضاء ويقرر النموذج من ينفّذ. لا كود توجيه صريح — القرار داخل النموذج. `mode="coordinate"` هو الوضع الوحيد المصرّح به في المستودع.
**ملاحظة:** هذا هو النمط الوحيد الذي يمنحك تعاوناً حقيقياً بأقل كود (7 أسطر)، لكنه يخفي التوجيه عن المراقبة والاختبار.

### النمط C — توجيه حتمي عبر JSON من وكيل triage
**الدليل:** `ag2_adaptive_research_team/router.py:31-60`.
```python
triage_prompt = f"""Question: {question}\n{doc_summary}\n
Decide the best route. Output JSON with keys: route: "local" or "web", confidence, rationale"""
triage = _extract_json(run_agent(agents["triage"], triage_prompt))
route = triage.get("route", "local")
if not local_chunks and web_enabled: route = "web"
```
ثم تفريع Python: `run_searxng(...)` أو البحث المحلي، وجمع `evidence`، ثم مسودة جواب.
**الوصف:** النموذج يقترح، والكود يقرر. يوجد أيضاً **قاعدة تجاوز** (إن لم توجد قطع محلية → web) تعلو على قرار النموذج. هذا أنظف نمط توجيه في المستودع من ناحية القابلية للاختبار.

### النمط D — تفريع متوازٍ ثم تجميع (Mixture-of-Agents)
**الدليل:** `starter_ai_agents/mixture_of_agents/mixture-of-agents.py:43-57`.
`results = await asyncio.gather(*[run_llm(m) for m in reference_models])` ثم نموذج aggregator يصوغ إجابة واحدة من كل الردود.
**الوصف:** تعاون "رأي جماعي" لا تفويض مهام. مفيد أكاديمياً (مراجعة متقاطعة)، مكلف حسابياً.

### النمط E — المعرفة المشتركة بدل تمرير الرسائل
**الأدلة:** `local_legal_agent.py:120-135` (نفس `knowledge_base` تُمرَّر للفريق وللأعضاء مع `search_knowledge=True`)؛ `voice_rag/rag_voice.py:212-224` (نص سياق يدوي واحد)؛ `local_hybrid_search_rag/local_main.py:240-247` (`search=hybrid_search` كـ callback داخل `rag()`).
**الوصف:** الوكلاء لا يتحدثون؛ يشتركون في مصدر حقيقة واحد. هذا هو النمط السائد في المستودع كله، وهو الأرخص والأوضح للأنظمة الأكاديمية.

### النمط F — الحالة: جلسة، أم SQLite، أم ذاكرة دلالية
**الأدلة:** `local_chatgpt_memory.py:44-46` (سجل العرض في `st.session_state` فقط)؛ `local_hybrid_search_rag/local_main.py:207-222` (سجل الجلسة يُحوَّل إلى `messages`)؛ `finance_agent_team.py:10,18,29` (`SqliteDb` + `add_history_to_context=True`)؛ `local_chatgpt_memory.py:8-27` (mem0/Qdrant).
**الوصف:** ثلاث درجات استمرارية: تضيع مع إعادة التشغيل / تبقى على القرص / تُسترجَع دلالياً. لا يوجد في المستودع نمط "سجل خام + استرجاع دلالي معاً" — إما هذا أو ذاك.

---

## 5. ملاحظات حرجة (فجوات بين الادعاء والكود)

1. **"فريق" التعليم ليس فريقاً برمجياً.** لا `Team`، لا تمرير مخرجات، لا أدوات مشتركة. إن أردت نظاماً أكاديمياً حقيقياً، ستحتاج بناء سلسلة `Professor → Advisor → Librarian → TA` بنفسك (تمرير `professor_response.content` إلى تعليمات الوكيل التالي)، أو استخدام `Team(mode="coordinate")`.
2. **الوكيل الصوتي ليس محلياً.** التضمين محلي (fastembed) لكن LLM وTTS عبر OpenAI. إن كان "بلا API مدفوع" شرطاً صارماً، هذا التطبيق مرجع بنيوي فقط؛ البديل العملي هو Piper/Coqui محلياً + نفس خط الأنابيب.
3. **RAG المحلي في `local_rag_agent` لا يضبط الاسترجاع.** لا `num_results`، لا rerank، لا hybrid. للمواد الأكاديمية الكثيفة ستحتاج النسخة الهجينة (3.5) أو ضبط agno يدوياً.
4. **`local_chatgpt_with_memory` لا يمرّر تاريخ المحادثة.** الاعتماد كلي على استرجاع mem0؛ الأسئلة التتبعية القصيرة ("وماذا عن الفصل الثاني؟") قد تفشل لأن الذاكرة الدلالية لا تحفظ تسلسل الحوار.
5. **النسخة الهجينة تفترض PostgreSQL** في واجهتها واعتمادياتها، وهذا يخالف هدف "خفيف الاعتماديات" — الحل: تمرير `sqlite:///raglite.db` إن قبلها RAGLite (سلوك المكتبة خارج نطاق هذا المسح، يحتاج تحققاً عملياً).

---

## 6. توصية معمارية لنظام خفيف الاعتماديات (مبنية على ما سبق)

**المبدأ:** لا إطار وكلاء. الوكلاء دوال Python، والتوجيه كود صريح، والسياق نص يُبنى في مكان واحد.

**المكوّنات (4 مكتبات فقط):**
- `streamlit` — واجهة الشات (`st.chat_message` / `st.chat_input` / `st.session_state`، كما في 3.3 و3.5).
- `openai` — عميل فقط، موجّه إلى Ollama عبر `base_url="http://localhost:11434/v1"` (نمط `llama3_stateful_chat`). صفر تكلفة، وواجهة برمجية موحدة تسمح بالتبديل لاحقاً.
- `qdrant-client` أو `sqlite-vec` — مخزن المتجهات محلياً على `localhost:6333` (نمط 3.2 و3.3).
- `rank_bm25` — الجزء المعجمي من البحث الهجين (بديل خفيف عن RAGLite).

**خط الأنابيب المقترح:**
1. **الفهرسة:** PDF → تقطيع 512/تداخل 64 → تضمين Ollama (`nomic-embed-text`) → Qdrant.
2. **البحث الهجين:** BM25 + متجهي → دمج بـ RRF → إبقاء أفضل 5.
3. **التوجيه الحتمي:** دالة `route(question, chunks)` تعيد `"rag"` أو `"general"` بقاعدة صريحة (نمط C مصغّراً، بلا وكيل triage) — أرخص وأسهل اختباراً.
4. **الوكلاء كدوال:** `professor()`, `advisor()`, `librarian()`, `ta()`، كل واحدة تستلم `(question, context)` وتعيد نصاً، وتُمرَّر مخرجة كل واحدة كسياق للتالية (إصلاح فجوة النمط A).
5. **الحالة:** SQLite لسجل الرسائل الخام + Qdrant لملخصات الجلسات (يجمع النمطين E/F).

**ما تأخذه من كل تطبيق:**
- من 3.1: صياغة `role` + `instructions` لكل وكيل، وتسلسل الخطوات.
- من 3.2: أبسط اقتران `Knowledge → Agent` و`AgentOS` كواجهة أولية.
- من 3.3: عزل الذاكرة بـ `user_id` وبناء نص السياق قبل الاستدعاء.
- من 3.4: كشف أبعاد التضمين عملياً + بث الصوت (إن أضفت صوتاً لاحقاً).
- من 3.5: `hybrid → retrieve → rerank → generate` + fallback الصريح + بث المؤشر.

---

## 7. حدود هذا المسح (ما لم أتحقق منه)

- لم أشغّل أي تطبيق ولم أختبر سلوك agno الداخلي (كيف يقرر `Team` الأعضاء، وكيف يحقن `Knowledge` القطع). كل ما قيل عن السلوك الداخلي مأخوذ من أسماء المعاملات، لا من تنفيذ.
- لم أفحص بقية مجلدات `advanced_ai_agents/agent_teams` (17 مجلداً) إلا للبحث عن أنماط `Team`. قد توجد أنماط إضافية في `ai_recruitment_agent_team` أو `multimodal_*`.
- لم أتحقق من دعم RAGLite لـ SQLite فعلياً (بند 5.5).
- أرقام الأسطر تشير إلى الحالة الحالية للملفات في مساحة العمل، وقد تتغير مع تحديثات المستودع.
