"""قاعدة المعرفة الأساسية (Seed Knowledge) — تُدمج تلقائياً في فهرس RAG.

تحتوي: كل الروابط المعطاة من إدارة الفريق (جروبات/درويفات/جامعة)، معلومات المستويات
والأقسام، الدفع والبنوك، السكن في اسيوط الجديدة، منصات التعلم والعمل الحر، ومعادلات GPA.
المبدأ: لا نكتب أي رقم أو موعد غير موثق — نوجّه دائماً للمصدر الرسمي.
"""
from __future__ import annotations

from .rag import chunk_text

GROUPS = [
    {"name": "جروب الواتساب الرسمي", "name_en": "Official WhatsApp Group", "url": "https://chat.whatsapp.com/BidB0EsNILVGLbExB2rdg0", "category": "جروبات", "category_en": "Groups"},
    {"name": "جروب التليجرام الرسمي", "name_en": "Official Telegram Group", "url": "https://t.me/+fHAUxVl3aSk0MDNk", "category": "جروبات", "category_en": "Groups"},
]

DRIVE_LINKS: list[dict] = [
    {"name": "درايف الترم الحالي", "name_en": "Current Term Drive", "url": "https://drive.google.com/drive/folders/1cuHprcMEC8Gm8a3i1wasCgmsm6VCJEZY", "category": "درويفات", "category_en": "Drives"},
    {"name": "الفرقة الأولى 2025 — الترم الأول (محاضرات وشيتات)", "name_en": "First Year 2025 — Term 1 (lectures & sheets)", "url": "https://drive.google.com/drive/folders/19SZxrcLIsZCjspjM4g0S3rrFPe2w3s4s", "category": "درويفات", "category_en": "Drives"},
    {"name": "الفرقة الأولى 2025 — الترم الثاني (محاضرات وشيتات)", "name_en": "First Year 2025 — Term 2 (lectures & sheets)", "url": "https://drive.google.com/drive/folders/1C7y_L3WOv1cLS9SjnQThbYOs4oqIHOsx", "category": "درويفات", "category_en": "Drives"},
    {"name": "السنة الأولى — الترم الأول", "name_en": "Year 1 — Term 1", "url": "https://drive.google.com/drive/folders/10ZVmDrwPinB-ujyOInwlO6wWNnn3WkYB", "category": "درويفات", "category_en": "Drives"},
    {"name": "السنة الأولى — الترم الثاني", "name_en": "Year 1 — Term 2", "url": "https://drive.google.com/drive/folders/10flE34lH_ssb24LWQ4bZWgJo3oR7dFzj", "category": "درويفات", "category_en": "Drives"},
    {"name": "السنة الثانية — الترم الأول", "name_en": "Year 2 — Term 1", "url": "https://drive.google.com/drive/folders/10gkYb3GhImBPWEBpcbA18a1QAGGroM2q", "category": "درويفات", "category_en": "Drives"},
    {"name": "السنة الثانية — الترم الثاني", "name_en": "Year 2 — Term 2", "url": "https://drive.google.com/drive/folders/10hr9YV_f67TBjmQpK6R0ghBAj2FyQ-lJ", "category": "درويفات", "category_en": "Drives"},
    {"name": "Level 2 — الترم الأول", "name_en": "Level 2 — Term 1", "url": "https://drive.google.com/drive/folders/1fKYEDTr1Eu0SCkuudy26FpM6AbTWluPd", "category": "درويفات", "category_en": "Drives"},
    {"name": "Level 2 — الترم الثاني", "name_en": "Level 2 — Term 2", "url": "https://drive.google.com/drive/folders/10ZtkfiQC1GH_t0orRAka8jMM4L1Psdd6", "category": "درويفات", "category_en": "Drives"},
]

UNIV_LINKS: list[dict] = [
    {"name": "منصة الطلاب — Sphinx University (sls)", "name_en": "Student Portal — Sphinx University (sls)", "url": "https://sls.sphinx.edu.eg/Login.aspx", "category": "جامعة", "category_en": "University"},
    {"name": "دليل طالب كلية الحاسبات والذكاء الاصطناعي (PDF)", "name_en": "Computers & AI Faculty Student Guide (PDF)", "url": "https://drive.google.com/file/d/1Fm46Gd8N1dHNmDkLgjG04IicYLYgi5xf/view", "category": "جامعة", "category_en": "University"},
    {"name": "جدول سنة أولى حاسبات (PDF)", "name_en": "First-Year CS Schedule (PDF)", "url": "https://drive.google.com/file/d/197nXoKbNrsp_lhiietiANsLxS6_z7zdD/view", "category": "جامعة", "category_en": "University"},
    {"name": "محادثة مرجعية (DeepSeek) للتحضير", "name_en": "Reference conversation (DeepSeek)", "url": "https://chat.deepseek.com/share/rmi0tpitlc5u9b8wv0", "category": "مراجع", "category_en": "References"},
]

ALL_LINKS = GROUPS + DRIVE_LINKS + UNIV_LINKS

SEED: list[dict] = [
    {
        "title": "عن النظام وفريق الوكلاء",
        "text": (
            "هذا النظام هو فريق وكلاء ذكاء اصطناعي متعدد (Multi-Agent System) يخدم طلاب كليات الحاسبات "
            "والذكاء الاصطناعي في جامعة سفنكس وجامعة اسيوط الأهلية وجامعة اسيوط. المنسّق يستقبل سؤالك "
            "ويوجّهه للوكيل المتخصص الأنسب، ويمكن لأكثر من وكيل التعاون في نفس الإجابة. الوكلاء: المرشد "
            "الأكاديمي (المواد واللائحة والتسجيل)، مخطط المذاكرة، وكيل الحسابات (GPA)، وكيل الشؤون المالية "
            "(المصاريف والدفع)، وكيل الحياة الجامعية (الجروبات والروابط والخدمات)، وكيل السكن والخدمات "
            "في اسيوط الجديدة، وكيل المهنة (CV وLinkedIn والعمل الحر)، وكيل مصادر التعلم (كورسات وقنوات)، "
            "ووكيل البحث العام (أسئلة عامة وبحث إنترنت). كل إجابة تأتي بمصادرها، ويمكنك مراجعة سابقة "
            "أسئلتك من سجل المحادثات في أي وقت."
        ),
    },
    {
        "title": "الجروبات الرسمية للتواصل",
        "text": (
            "جروب الواتساب الرسمي: https://chat.whatsapp.com/BidB0EsNILVGLbExB2rdg0\n"
            "جروب التليجرام الرسمي: https://t.me/+fHAUxVl3aSk0MDNk\n"
            "انضم للجروبات لتصلك الإعلانات والجدول والشيتات فوراً، ولو زرلك لينك اسأل الوكيل يعيد إرساله."
        ),
    },
    {
        "title": "روابط الدرويفات — محاضرات وشيتات كل الترمات",
        "text": (
            "درايف الترم الحالي: https://drive.google.com/drive/folders/1cuHprcMEC8Gm8a3i1wasCgmsm6VCJEZY\n"
            "الفرقة الأولى 2025 ترم أول: https://drive.google.com/drive/folders/19SZxrcLIsZCjspjM4g0S3rrFPe2w3s4s\n"
            "الفرقة الأولى 2025 ترم ثانٍ: https://drive.google.com/drive/folders/1C7y_L3WOv1cLS9SjnQThbYOs4oqIHOsx\n"
            "السنة الأولى ترم أول: https://drive.google.com/drive/folders/10ZVmDrwPinB-ujyOInwlO6wWNnn3WkYB\n"
            "السنة الأولى ترم ثانٍ: https://drive.google.com/drive/folders/10flE34lH_ssb24LWQ4bZWgJo3oR7dFzj\n"
            "السنة الثانية ترم أول: https://drive.google.com/drive/folders/10gkYb3GhImBPWEBpcbA18a1QAGGroM2q\n"
            "السنة الثانية ترم ثانٍ: https://drive.google.com/drive/folders/10hr9YV_f67TBjmQpK6R0ghBAj2FyQ-lJ\n"
            "Level 2 ترم أول: https://drive.google.com/drive/folders/1fKYEDTr1Eu0SCkuudy26FpM6AbTWluPd\n"
            "Level 2 ترم ثانٍ: https://drive.google.com/drive/folders/10ZtkfiQC1GH_t0orRAka8jMM4L1Psdd6\n"
            "اطلب من الوكيل أي مادة أو شيت بالاسم وسيرشدك للمصدر المناسب."
        ),
    },
    {
        "title": "منصة الجامعة والدليل والجدول",
        "text": (
            "منصة الطلاب في جامعة سفنكس (الدخول ببياناتك الجامعية): https://sls.sphinx.edu.eg/Login.aspx\n"
            "دليل طالب كلية الحاسبات والذكاء الاصطناعي (PDF): https://drive.google.com/file/d/1Fm46Gd8N1dHNmDkLgjG04IicYLYgi5xf/view\n"
            "جدول سنة أولى حاسبات (PDF): https://drive.google.com/file/d/197nXoKbNrsp_lhiietiANsLxS6_z7zdD/view\n"
            "محادثة مرجعية للتحضير (DeepSeek): https://chat.deepseek.com/share/rmi0tpitlc5u9b8wv0\n"
            "من المنصة تسجل المواد، وتشوف درجاتك، وتدفع المصاريف، وتتابع الإعلانات الرسمية."
        ),
    },
    {
        "title": "الجامعات: سفنكس واسيوط الأهلية واسيوط",
        "text": (
            "جامعة سفنكس (Sphinx University): جامعة خاصة مقرها اسيوط الجديدة، ومنها كلية الحاسبات "
            "والذكاء الاصطناعي، ومنصتها الطلابية sls.sphinx.edu.eg.\n"
            "جامعة اسيوط الأهلية: جامعة أهلية في اسيوط الجديدة ببرامج حديثة تشمل حاسبات وذكاء اصطناعي.\n"
            "جامعة اسيوط (الحكومية): من أقدم جامعات صعيد مصر وموقعها الرسمي aun.edu.eg ولها كلية "
            "حاسبات ومعلومات.\n"
            "القاعدة الذهبية: أي معلومة رسمية (قبول، مصاريف، مواعيد، لائحة) راجعها من موقع الجامعة أو "
            "شؤون الطلاب، ويمكن للوكيل البحث في الإنترنت ليأتيك بالمصدر."
        ),
    },
    {
        "title": "المستويات والأقسام ومسار التخصص",
        "text": (
            "المستويان الأول والثاني: أساسيات (برمجة، رياضيات، هياكل بيانات، شبكات...).\n"
            "المستوى الثالث Level 3: تختار فيه تخصصك: AI أو Cyber Security أو Bioinformatics.\n"
            "لو شاطر في الرياضيات والاحصاء والاحتمالات وML وPython وNLP وDeep Learning → AI مناسب لك.\n"
            "لو بتحب الشبكات وأنظمة التشغيل وLinux وتحليل الثغرات → Cyber Security مناسب لك.\n"
            "لو بتحب الأحياء والكيمياء مع تحليل البيانات وPython → Bioinformatics مناسب لك.\n"
            "المستوى الرابع Level 4: مشروع التخرج + تخصصات متقدمة، وشروط تسجيل مشروع التخرج من "
            "اللائحة الأكاديمية ودليل الطالب.\n"
            "اسأل الوكيل الأكاديمي عن ساعات أي مادة، وهل لها معمل/سكشن، ونظري أم عملي."
        ),
    },
    {
        "title": "المصاريف والدفع والبنوك والمحافظ الإلكترونية",
        "text": (
            "وسائل الدفع الشائعة للرسوم الجامعية في مصر: InstaPay (تطبيق مجاني للتحويل البنكي)، فودافون "
            "كاش، WE Pay، Orange Cash، Etisalat Cash، بطاقة ميزة، والتحويل أو الإيداع في بنوك مثل بنك مصر "
            "وQNB الدولي وCIB والبنك الأهلي.\n"
            "مواعيد الدفع والغرمات وطرق السداد المعتمدة بالجامعة تُعلن رسمياً في منصة الطلاب "
            "sls.sphinx.edu.eg وإعلانات شؤون الطلاب — لا تعتمد على أي معلومة غير رسمية.\n"
            "لو اتأخرت في الدفع تواصل مع شؤون الطلاب فوراً لمعرفة آلية الاعتماد والمدد. اسأل الوكيل "
            "المالي عن خطوات الدفع عبر InstaPay أو المحافظ خطوة بخطوة."
        ),
    },
    {
        "title": "السكن في اسيوط الجديدة (شمال الجمعة والرحاب وما حولها)",
        "text": (
            "المناطق الأقرب لجامعة سفنكس وجامعة اسيوط الأهلية في اسيوط الجديدة تشمل: منطقة شمال "
            "الجمعة، منطقة الرحاب، والأحياء السكنية المحيطة بالجامعات والمعاهد، إضافة لسكن الجامعة "
            "الإن لم يكن مكتظاً.\n"
            "نصائح قبل الإيجار: عاين الشقة بنفسك، اتفق على عقد مكتوب، اسأل عن العدادات (كهربا/ميه/غاز)، "
            "قرب المواصلات والأمن والإنترنت، ولو بتشارك اتباعوا تقسيم المصاريف كتابةً.\n"
            "الأسعار متغيرة بحسب الموسم والتشطيب والفرش — اسأل وكيل السكن يبحث لك في الإنترنت وخرائط "
            "جوجل عن السوق الحالي، وقارن أكثر من عرض قبل القرار. شباب وبنات يفضلوا مناطق آمنة وقريبة، "
            "وفي عمارات مخصصة للبنات في أغلب المناطق — اسأل الوكيل بالتفصيل."
        ),
    },
    {
        "title": "الخدمات اليومية حول الجامعات في اسيوط الجديدة",
        "text": (
            "حول الجامعات تلاقي: مطاعم وكافيهات دليفري، صيدليات (بعضها 24 ساعة)، مستشفيات ومراكز طبية، "
            "سوبر ماركت ومخابز، ملاعب (قدم/سلة)، محلات قرطاسية، ومصارف وأجهزة صراف آلي.\n"
            "اسأل وكيل السكن والخدمات باسم المنطقة (مثلاً: أقرب صيدلية لشمال الجمعة؟) وسيرشدك مباشرة، "
            "ويفضل دائماً مراجعة التقييمات على خرائط جوجل قبل الاعتماد على أي مكان. الوكيل يستطيع البحث "
            "في الإنترنت لإحضار الأماكن الحالية والتقييمات عند تفعيل البحث."
        ),
    },
    {
        "title": "حساب المعدل التراكمي GPA والمعادلات",
        "text": (
            "المعادلة الأساسية: GPA = مجموع (نقاط المادة × الساعات المعتمدة) ÷ مجموع الساعات.\n"
            "سلّم 5 نقاط (شائع في جامعات مصرية): ممتاز = 5.0، جيد جدا = 4.0، جيد = 3.0، مقبول = 2.0، "
            "ضعيف = 1.0، راسب = 0.0.\n"
            "سلّم 4 نقاط (American/Standard): A=4.0، A-=3.7، B+=3.3، B=3.0، B-=2.7، C+=2.3، C=2.0، "
            "C-=1.7، D+=1.3، D=1.0، F=0.0.\n"
            "النسبة المئوية التقديرية = GPA ÷ أقصى نقاط × 100. التقديرات المصرية الشائعة: 85% فأكثر "
            "ممتاز، 75-85 جيد جدا، 65-75 جيد، 50-65 مقبول.\n"
            "للحساب الفوري والدقيق استخدم زر حاسبة GPA في الواجهة — يكفي تدخل التقدير والساعات لكل "
            "مادة، ويحسب لك المعدل الترمي والتراكمي. بعض الجامعات لها سلالم خاصة فراجع اللائحة."
        ),
    },
    {
        "title": "بناء CV احترافي متوافق مع ATS",
        "text": (
            "ATS هو نظام الفرز الآلي للسير الذاتية في الشركات. قواعده الذهبية: ملف نصي واضح بدون جداول "
            "معقدة أو صور، عناوين قياسية (Summary, Education, Skills, Experience, Projects)، كلمات "
            "مفتاحية مطابقة لوصف الوظيفة، أفعال قوية (Built, Developed, Analyzed...)، وأرقام تقيس أثرك، "
            "وطول مناسب (صفحة إلى صفحتين).\n"
            "استخدم أداة CV في الواجهة (زر 💼): تدخل بياناتك وتخصصك فيحلل النظام نقاط قوة CV ويقيس "
            "درجة التوافق ATS ويولد لك سيرة جاهزة: نسخة HTML للطباعة PDF ونسخة DOCX قابلة للتعديل.\n"
            "للطلاب: أبرز المشروعات والتدريبات والأنشطة لأنها تعوض قلة الخبرة، وأضف رابط GitHub."
        ),
    },
    {
        "title": "منصات التعلم والتدريب المجانية",
        "text": (
            "NTI (المعهد القومي للاتصالات): كورسات شبكات واتصالات ودورات معتمدة — nti.sci.eg\n"
            "ITI (معهد تكنولوجيا المعلومات): منح صيفية وشتوية شهرية مجانية في البرمجة والشبكات والأمن — "
            "iti.gov.eg وافتح باب التقديم كل سنة.\n"
            "Cisco Networking Academy: كورسات CCNA وNetwork Basics وCyberSecurity — netacad.com\n"
            "Google: grow.google وSkillshop للشهادات المجانية.\n"
            "منصات عامة: Coursera وedX (مراجعة مجانية للأكواد) وUdemy (عروض مستمرة).\n"
            "قنوات يوتيوب عربية قوية: Elzero Web School (ويب)، Codezilla (بايثون وعلوم حاسب)، "
            "Adel Nasim (برمجة وشبكات) — وابحث باسم المادة بالعربي/الإنجليزي."
        ),
    },
    {
        "title": "منصات العمل الحر وبداية الدخل",
        "text": (
            "عربياً: مستقل mostaql.com (مشاريع)، خمسات khamsat.com (خدمات مصغرة)، نفذلي neftly وأريد "
            "ureed.me وكفيل — ابدأ بخدمة واضحة بسعر تنافسي وجمع تقييمات.\n"
            "عالمياً: Upwork وFiverr وFreelancer.com وKwork وToptal (للمحترفين).\n"
            "نصائح: بورتفوليو على GitHub وصفحة شخصية، عرض يبدأ بمشكلة العميل لا بمهاراتك، تواصل سريع "
            "وبأدب، سلم تسليم واضح، واحتفظ بأثباتات العمل. اسأل وكيل المهنة عن خطة 30 يوم لبدء العمل الحر "
            "في تخصصك (AI أو Cyber أو ويب أو بيانات)."
        ),
    },
    {
        "title": "تطوير GitHub وLinkedIn",
        "text": (
            "GitHub: اجعل أفضل 6 مشاريع Pinned، وكل مشروع README واضح (المشكلة، التقنيات، صور، تشغيل)، "
            "commits منتظمة، وشارك أكواد مسابقات أو حلول مواد منظمة.\n"
            "LinkedIn: صورة احترافية، Headline يوضح تخصصك (مثال: AI Student | Python & ML)، About يحكي "
            "قصة مشروعاتك، Skills مطابقة لسوق العمل، تفاعل أسبوعي (منشور عن مشروع أو ملخص تعلم)، وتواصل "
            "مع مهندسين وموظفي توظيف في الشركات المستهدفة.\n"
            "اسأل وكيل المهنة يراجع ملفك ويعطيك خطة تحسين خطوة بخطوة."
        ),
    },
    {
        "title": "التدريب الميداني ومشروعات التخرج",
        "text": (
            "التدريب الميداني: ابدأ بالبحث مبكراً في الشركات المحلية ومركز ITI وNTI وشركات العمل عن بعد، "
            "جهز CV قوي من أداة CV، وخطاب تقديم قصير مخصص لكل جهة، وتابع Wuzzuf وLinkedIn للفرص.\n"
            "مشروع التخرج (Level 4): اختر مشكلة حقيقية، حدد نطاقاً تنفذه فعلاً، وثّق في GitHub، وقسم "
            "الأدوار داخل الفريق، واحضر Demo كل أسبوعين. أفكار AI: مساعد جامعي ذكي، تحليل صور طبية، "
            "نظام كشف غش في الامتحانات. أفكار Cyber: SOC صغير مراقب سجلات، تحليل تصيد، مختبر اختراق "
            "آمن. أفكار Bioinformatics: تحليل جينوم مبسط أو تنبؤ بروتيني.\n"
            "اسأل الوكيل يقترح عليك أفكاراً مناسبة لقسمك ومستواك."
        ),
    },
    {
        "title": "كيف تدرّب الفريق على ملفاتك",
        "text": (
            "ضع أي ملفات (PDF، Word، Excel، PowerPoint، CSV، صور) في مجلد data داخل مجلد البرنامج، أو "
            "أرفقها في الشات مع تفعيل خيار (تدريب الفريق على هذه الملفات)، ثم اضغط زر تحديث الفهرس.\n"
            "بعد الفهرسة يصبح الفريق قادراً على الإجابة من محتوى محاضراتك وشيتاتك وجداولك بالتفصيل "
            "والمصادر. للتنزيل التلقائي لدرويفات جوجل استخدم سكربت الفهرسة python ingest.py --download."
        ),
    },
]


def build_knowledge_chunks() -> list[dict]:
    """يحول القاعدة الأساسية + كل الروابط إلى مقاطع قابلة للبحث."""
    docs: list[dict] = []
    for s in SEED:
        docs.extend(chunk_text(s["text"], source="المعرفة-الأساسية", title=s["title"]))
    # بطاقات روابط مستقلة لكل رابط (دقة أعلى في الاسترجاع)
    for link in ALL_LINKS:
        docs.append({
            "source": "الروابط",
            "title": link["name"],
            "text": f"[{link['category']}] {link['name']}: {link['url']}",
        })
    return docs
