# مكوّن الـ Avatar — مشغل الفيديو وربطه بالرد

> الجزء الخاص بـ **عبدالرحمن** — الفريق الثاني (Frontend & Multimedia): عرض الفيديو،
> توحيد الهوية البصرية، التجاوب، واختبار الواجهة.

---

## 1. الفكرة

لوحة عائمة (floating dock) تظهر أسفل الصفحة في الجهة المقابلة للشريط الجانبي:

- **الديسكتوب:** بطاقة 268px برأس (اسم الوكيل + حالته) وشاشة فيديو 1:1 وشريط تحكم.
- **التابلت (≤860px):** 232px.
- **الموبايل (≤520px):** فقاعة صغيرة 122px أثناء الرد حتى لا تغطي نص الإجابة،
  وتتوسّع باللمس إلى البطاقة الكاملة.
- عند عدم الاستخدام تُطوى إلى **orb** دائري 62px يبقى في نفس المكان.

تفتح تلقائيًا مع بداية أي رد، وتُطوى تلقائيًا بعد **4.2 ثانية** من العودة لحالة `idle`
(إلا إذا ثبّتها المستخدم بزر التثبيت).

---

## 2. الملفات

| الملف | الوظيفة |
|---|---|
| `web/avatar.js` | المكوّن كاملًا: البناء، الحالات، المشغل، تحليل الصوت، الذاكرة المحلية |
| `web/avatar.css` | التنسيق والحركات والاستجابة (يقرأ tokens من `style.css`) |
| `web/assets/avatar/idle.mp4` | مقطع التنفّس/الرمش (4 ثوانٍ، 30fps، 512×512) |
| `web/assets/avatar/talk.mp4` | مقطع الكلام (فتح/إغلاق الفم + إيماءة رأس) |
| `web/assets/avatar/poster.jpg` | أول إطار — يظهر قبل تحميل الفيديو |
| `tools/avatar_gen.py` | مولّد المقطعين (Pillow + ffmpeg) لإعادة إنتاجهما أو تعديل الألوان |
| `web/qa/viewport-preview.html` | صفحة QA لمعاينة الواجهة على مقاسات مختلفة |

المكوّن مضاف في `index.html` قبل `app.js`:

```html
<link rel="stylesheet" href="/static/avatar.css?v=2">
...
<script src="/static/avatar.js?v=2"></script>
<script src="/static/app.js?v=7"></script>
```

---

## 3. الحالات

```
idle ──(بدء رد)──▶ thinking ──(أول محتوى)──▶ speaking ──(done)──▶ idle
  ▲                    │                        │
  └────(خطأ)── error ◀─┘                        │
  └────────────(إدخال صوتي)── listening ◀───────┘
```

| الحالة | ما يظهر | من أين تُطلق |
|---|---|---|
| `idle` | «جاهز للمساعدة»، مقطع idle | `finalizeStream` / نهاية TTS |
| `thinking` | «بيفكر…»، نقطة ذهبية، مقطع idle | `streamChat` + حدث `route` + `thinking` |
| `speaking` | «بيتكلم»، مقطع talk، مؤشر صوت | أول حدث `content` / TTS / `speechSynthesis` |
| `listening` | «بيسمعك…»، نقطة حمراء | `startVoice()` |
| `error` | «تعذّر التشغيل» | حدث `error` من الـ SSE |

كل انتقال يُطلق حدثًا على `document` اسمه `avatarstate` مع `detail.state` (مفيد للاختبار).

---

## 4. الواجهة البرمجية

```js
AvatarStage.setState("thinking" | "listening" | "speaking" | "idle" | "error");
AvatarStage.setAgent({ name: "المرشد الأكاديمي", role: "يراجع اللائحة" });
AvatarStage.open();        // فتح + تثبيت
AvatarStage.collapse();    // طي إلى orb
AvatarStage.wake();        // فتح بدون تثبيت (يُستخدم داخليًا)
AvatarStage.toggle();      // زر الشريط العلوي
AvatarStage.bindAudio(el); // ربط عنصر <audio> بـ analyser لتحريك الفم
AvatarStage.unbindAudio();
AvatarStage.isOpen();      // boolean
```

نقاط الربط الموجودة في `app.js`:

| الموضع | الاستدعاء |
|---|---|
| `streamChat()` | `setState("thinking")` بعد إنشاء رسالة الوكيل |
| `consumeSSE()` → `route` | `setAgent({name, role})` + `thinking` |
| `consumeSSE()` → أول `content` | `speaking` |
| `consumeSSE()` → `error` | `error` |
| `finalizeStream()` | `idle` |
| `speak()` (TTS) | `bindAudio(curAudio)` / `unbindAudio()` + `idle` |
| `startVoice()` / `stopVoice()` | `listening` / `idle` |
| `init()` | ربط زر `#avatarBtn` بالتبديل |

---

## 5. مشغل الفيديو

- عنصران `<video>` — أحدهما لمقطع idle والآخر talk — والتبديل بينهما بـ cross-fade 320ms
  حتى لا «يقفز» الـ avatar عند بدء الكلام.
- `muted` افتراضيًا (سياسة المتصفح تمنع التشغيل التلقائي بغير كتم)، وزر الصوت يفتح الصوت
  على المقطع النشط فقط.
- أدوات: تشغيل/إيقاف، إعادة من البداية، شريط تقدم (نقر + سحب + أسهم لوحة المفاتيح)،
  الوقت الحالي، كتم، ملء الشاشة (Fullscreen API على `.av-screen`).
- الأدوات نفسها تبقى **LTR** في الواجهة العربية (مثل أي مشغل فيديو)، والبطاقة نفسها RTL.
- عند إخفاء التبويب يتوقف الفيديو (`visibilitychange`) توفيرًا للمعالجة، ويكمل عند العودة.
- `data-playing="1|0"` على العنصر الجذر يعكس حالة التشغيل الفعلية (للاختبار الآلي).

### اكتشاف الأصول والبديل

عند التحميل يفحص المكوّن بطلب `HEAD`:

1. `/static/assets/avatar/idle.mp4` و`talk.mp4`
2. ثم `/static/assets/avatar/avatar.mp4` (مقطع واحد للكل)

إن لم يوجد أي ملف (أو فشل التحميل) يتحوّل تلقائيًا إلى **avatar مرسوم SVG** بنفس الهوية:
تنفّس، رمش كل ~5 ثوانٍ، فتح فم أثناء الكلام، وإيماءات رأس في حالة التفكير.
هذا يضمن أن الواجهة لا تظهر «شاشة سوداء» قبل أن يسلّم فريق الميديا الفيديو النهائي.

---

## 6. تحريك الفم مع الصوت الحقيقي

عند تشغيل TTS:

```js
const ctx = new AudioContext();
const src = ctx.createMediaElementSource(audioEl);
const analyser = ctx.createAnalyser();
src.connect(analyser); analyser.connect(ctx.destination);
```

يُحسب RMS كل إطار ويُمرَّر إلى CSS:

```css
--av-mouth: 0.42;          /* يحرّك scaleY للفم */
#avatarStage[data-audio="1"] .av-eq { opacity: 1; }  /* مؤشر مستوى الصوت */
```

لو رفض المتصفح التحليل (CORS/سياسة)، يعود إلى حركة الفم CSS الافتراضية بدون خطأ ظاهر.

---

## 7. استبدال الفيديو بآخر حقيقي (تسليم فريق الميديا)

المواصفات المطلوبة:

| البند | القيمة |
|---|---|
| المقاس | مربّع 1:1 — 512×512 كحد أدنى، ويفضّل 1024×1024 |
| المدة | 4–6 ثوانٍ قابلة للتكرار بدون «قطع» |
| الترميز | H.264 / yuv420p / mp4 (`-movflags +faststart`) |
| الحجم | أقل من 2MB لكل مقطع |
| الصوت | بدون صوت (المكوّن يتحكم بالصوت من TTS) |
| الخلفية | داكنة أو شفافة بصريًا بما يناسب الثيمين |

الخطوات: ضع `idle.mp4` و`talk.mp4` في `web/assets/avatar/` ثم أعد تحميل الصفحة —
لا حاجة لأي تعديل في الكود. الملفان الحاليان مولّدان بـ `tools/avatar_gen.py` ويمكن
استبدالهما في أي وقت.

لإعادة توليد المقطعين الحاليين:

```bash
python tools/avatar_gen.py
```

---

## 8. الوصولية (Accessibility)

- `role="region"` + `aria-label` للبطاقة، و`aria-live="polite"` لنص الحالة.
- كل زر له `aria-label` و`title`، وأزرار التبديل تستخدم `aria-pressed`.
- شريط التقدم: `role="slider"` + `aria-valuenow/valuetext` + تشغيل بالأسهم والمسافة.
- احترام `prefers-reduced-motion` عبر القاعدة العامة في `style.css`.
- أهداف اللمس ≥ 26px داخل المشغل و≥ 34px في الشريط العلوي.

---

## 9. روابط عرض سريعة

| الرابط | النتيجة |
|---|---|
| `/?avatar=1` | يفتح البطاقة مباشرة |
| `/?avatar=speaking` | يفتحها في وضع الكلام (مناسب للعرض التقديمي) |
| `/static/qa/viewport-preview.html?w=390&h=760&open=1&state=speaking` | معاينة على مقاس محدد |

---

## 10. قيود معروفة

1. **لا مزامنة شفاه حقيقية (lip-sync)** — تحتاج ملف فيديو بـ visemes أو مزوّد avatar
   (D-ID / HeyGen). الحل الحالي: مقطعان (idle/talk) + تحريك فم الـ SVG حسب شدة الصوت.
2. الفيديو لا يعمل في تبويب مخفي — سياسة المتصفح، وليس خطأ في المكوّن.
3. لا توجد مقاطع مخصّصة لكل وكيل بعد؛ يمكن إضافتها بتوسيع `CLIPS` في `avatar.js`.
4. TTS وإدخال الصوت لم يُختبرا صوتيًا في بيئة التطوير (لا يوجد مفتاح مزوّد ولا ميكروفون).
