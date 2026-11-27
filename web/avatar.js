/* ============================================================================
   AvatarStage — مشغل الـ Avatar وربطه بدورة الرد
   الفريق الثاني (Frontend & Multimedia) — عبدالرحمن: الفيديو وتجربة المستخدم
   ----------------------------------------------------------------------------
   • مشغل فيديو مستقل (تشغيل/إيقاف، شريط تقدم، كتم، إعادة، ملء الشاشة).
   • يتبدّل تلقائياً بين مقطعين: idle.mp4 و talk.mp4 حسب حالة الوكيل.
   • لو الملفات غير موجودة: يعرض avatar مرسوم بالـ SVG يتحرك (تنفّس/رمش/كلام).
   • يقرأ شدة الصوت الحقيقية من الـ TTS ويرسم حركة الفم (WebAudio analyser).
   • واجهة برمجية واحدة: AvatarStage.setState("thinking" | "speaking" | ...)

   الاستخدام من app.js:
     AvatarStage.setState("thinking");
     AvatarStage.setAgent({ name, role });
     AvatarStage.bindAudio(audioEl);  /  AvatarStage.unbindAudio();
   ========================================================================== */
(function () {
  "use strict";

  const BASE = "/static/assets/avatar/";
  const CLIPS = {
    idle: [BASE + "idle.mp4", BASE + "avatar.mp4"],
    talk: [BASE + "talk.mp4", BASE + "avatar.mp4"],
  };
  const LS = {
    pinned: "mas-avatar-pinned",
    hidden: "mas-avatar-hidden",
    muted: "mas-avatar-muted",
  };

  const I18N = {
    ar: {
      ready: "جاهز للمساعدة",
      listening: "بيسمعك…",
      thinking: "بيفكر…",
      speaking: "بيتكلم",
      error: "الفيديو مش متاح",
      name: "نور",
      role: "المساعد الأكاديمي",
      play: "تشغيل",
      pause: "إيقاف مؤقت",
      mute: "كتم الصوت",
      unmute: "تشغيل الصوت",
      full: "ملء الشاشة",
      exitFull: "إنهاء ملء الشاشة",
      open: "إظهار المساعد",
      collapse: "تصغير المساعد",
      close: "إغلاق المساعد",
      pin: "تثبيت المساعد مفتوحاً",
      unpin: "إلغاء تثبيت المساعد",
      seek: "شريط تقدم الفيديو",
      video: "فيديو المساعد",
      replay: "إعادة من البداية",
      zoom: "تكبير أو تصغير المساعد",
    },
    en: {
      ready: "Ready to help",
      listening: "Listening…",
      thinking: "Thinking…",
      speaking: "Speaking",
      error: "Video unavailable",
      name: "Nour",
      role: "Academic assistant",
      play: "Play",
      pause: "Pause",
      mute: "Mute",
      unmute: "Unmute",
      full: "Fullscreen",
      exitFull: "Exit fullscreen",
      open: "Show assistant",
      collapse: "Collapse assistant",
      close: "Close assistant",
      pin: "Keep assistant open",
      unpin: "Unpin assistant",
      seek: "Video progress",
      video: "Assistant video",
      replay: "Replay",
      zoom: "Expand or collapse assistant",
    },
  };

  const lang = () => {
    const l = (window.MAS && window.MAS.lang) || document.documentElement.lang || "ar";
    return l === "en" ? "en" : "ar";
  };
  const tr = (k) => (I18N[lang()][k] != null ? I18N[lang()][k] : I18N.ar[k] || k);
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : v; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  };

  /* ------------------------------------------------------------------ الرسم */
  function artSVG(prefix) {
    const p = "av" + prefix + "-";
    return `
<svg viewBox="0 0 240 240" role="img" aria-hidden="true" focusable="false">
  <defs>
    <radialGradient id="${p}bg" cx="50%" cy="10%" r="95%">
      <stop offset="0" stop-color="#1d3559"/><stop offset="58%" stop-color="#111d2f"/><stop offset="1" stop-color="#080d15"/>
    </radialGradient>
    <radialGradient id="${p}halo" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#4f8cff" stop-opacity=".34"/><stop offset="1" stop-color="#4f8cff" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="${p}skin" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f8d8bb"/><stop offset="1" stop-color="#e2b489"/>
    </linearGradient>
    <linearGradient id="${p}shirt" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#4180f5"/><stop offset="1" stop-color="#1d469f"/>
    </linearGradient>
    <linearGradient id="${p}hair" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#2d3444"/><stop offset="1" stop-color="#141922"/>
    </linearGradient>
    <linearGradient id="${p}rim" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#9dc0ff" stop-opacity=".6"/><stop offset="1" stop-color="#9dc0ff" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <rect width="240" height="240" fill="url(#${p}bg)"/>
  <circle cx="120" cy="94" r="98" fill="url(#${p}halo)"/>
  <circle cx="120" cy="120" r="105" fill="none" stroke="#4f8cff" stroke-opacity=".13" stroke-width="1.4" stroke-dasharray="2 9"/>

  <g class="av-chest">
    <path d="M32 246 C32 195 73 171 120 171 C167 171 208 195 208 246 Z" fill="url(#${p}shirt)"/>
    <path d="M120 171 V246" stroke="#12306b" stroke-opacity=".5" stroke-width="2"/>
    <path d="M103 176 q17 19 34 0 l7 6 q-24 24 -48 0 z" fill="#0e2350" opacity=".5"/>
  </g>

  <g class="av-head-g">
    <path d="M106 146 h28 v23 q-14 10 -28 0 z" fill="#d9a97f"/>
    <path d="M106 157 q14 10 28 0 v6 q-14 8 -28 0 z" fill="#c8956f" opacity=".5"/>
    <ellipse cx="78" cy="112" rx="8" ry="10" fill="#e9bd97"/>
    <ellipse cx="162" cy="112" rx="8" ry="10" fill="#e9bd97"/>

    <ellipse cx="120" cy="106" rx="44" ry="50" fill="url(#${p}skin)"/>
    <path d="M78 100 C80 70 97 56 118 55" stroke="url(#${p}rim)" stroke-width="3" fill="none" stroke-linecap="round"/>

    <path d="M76 108 C72 70 94 49 120 49 C148 49 168 70 166 108 C161 89 149 77 128 73 C119 71 108 74 98 82 C88 90 80 96 76 108 Z" fill="url(#${p}hair)"/>

    <g class="av-brow-g">
      <path d="M95 92 q9 -5 18 0" stroke="#2a2118" stroke-width="3" fill="none" stroke-linecap="round"/>
      <path d="M127 92 q9 -5 18 0" stroke="#2a2118" stroke-width="3" fill="none" stroke-linecap="round"/>
    </g>

    <g class="av-eyes-g">
      <ellipse cx="104" cy="108" rx="5.4" ry="6" fill="#1d2433"/>
      <ellipse cx="136" cy="108" rx="5.4" ry="6" fill="#1d2433"/>
      <circle cx="105.8" cy="105.7" r="1.7" fill="#fff" opacity=".92"/>
      <circle cx="137.8" cy="105.7" r="1.7" fill="#fff" opacity=".92"/>
      <circle cx="102.4" cy="110.2" r="1" fill="#fff" opacity=".45"/>
      <circle cx="134.4" cy="110.2" r="1" fill="#fff" opacity=".45"/>
    </g>

    <path d="M120 112 v12 q0 4 5 5" stroke="#cf9b74" stroke-width="2.6" fill="none" stroke-linecap="round"/>

    <g class="av-mouth-g">
      <path d="M108 138 q12 -6 24 0 q-12 13 -24 0 z" fill="#8e3f4a"/>
      <path d="M112 139 q8 2 16 0 q-8 5 -16 0 z" fill="#fff" opacity=".72"/>
    </g>

    <ellipse cx="92" cy="124" rx="9" ry="5" fill="#e08d7e" opacity=".16"/>
    <ellipse cx="148" cy="124" rx="9" ry="5" fill="#e08d7e" opacity=".16"/>

    <path d="M70 112 C70 63 92 43 120 43 C148 43 170 63 170 112" stroke="#d9b06a" stroke-width="4.4" fill="none" stroke-linecap="round" opacity=".95"/>
    <rect x="61" y="100" width="17" height="28" rx="8" fill="#222c3b" stroke="#d9b06a" stroke-width="2"/>
    <rect x="162" y="100" width="17" height="28" rx="8" fill="#222c3b" stroke="#d9b06a" stroke-width="2"/>
    <path d="M166 128 q-7 17 -25 16" stroke="#d9b06a" stroke-width="2.3" fill="none" stroke-linecap="round" opacity=".9"/>
    <circle cx="141" cy="144" r="3.2" fill="#d9b06a"/>
  </g>
</svg>`;
  }

  const TPL = `
  <div class="av-card" role="region" aria-label="">
    <div class="av-head">
      <span class="av-live" aria-hidden="true"></span>
      <div class="av-id"><b class="av-name">—</b><small class="av-role"></small></div>
      <button class="av-ico" data-av="pin" aria-pressed="false"><svg class="ic"><use href="#i-pin"/></svg></button>
      <button class="av-ico" data-av="min"><svg class="ic"><use href="#i-min"/></svg></button>
    </div>
    <div class="av-screen">
      <video class="av-video" data-slot="a" playsinline muted loop preload="none" poster="/static/assets/avatar/poster.jpg"></video>
      <video class="av-video" data-slot="b" playsinline muted loop preload="none" poster="/static/assets/avatar/poster.jpg"></video>
      <div class="av-art">${artSVG("main")}</div>
      <div class="av-scrim"></div>
      <div class="av-status"><span class="d"></span><span class="t" aria-live="polite">—</span></div>
      <button class="av-btn av-zoom" data-av="zoom"><svg class="ic"><use href="#i-expand"/></svg></button>
      <div class="av-eq" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></div>
      <div class="av-bar">
        <button class="av-btn" data-av="play"><svg class="ic"><use href="#i-play"/></svg></button>
        <button class="av-btn" data-av="replay" title=""><svg class="ic"><use href="#i-replay"/></svg></button>
        <div class="av-track" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="">
          <i class="av-fill"></i><b class="av-knob"></b>
        </div>
        <span class="av-time">0:00</span>
        <button class="av-btn" data-av="mute"><svg class="ic"><use href="#i-speaker"/></svg></button>
        <button class="av-btn" data-av="full"><svg class="ic"><use href="#i-expand"/></svg></button>
      </div>
    </div>
  </div>
  <button class="av-orb" data-av="open">
    <span class="face">${artSVG("orb")}</span>
    <span class="av-orb-dot" aria-hidden="true"></span>
  </button>`;

  /* ------------------------------------------------------------------ الحالة */
  const S = {
    root: null, els: {}, state: "idle", open: false, pinned: false, hidden: false,
    agent: null, mode: "art", clips: {}, active: "a", muted: true, raf: 0,
    collapseTimer: 0, audioCtx: null, analyser: null, srcNode: null, freq: null, audioRaf: 0,
  };

  function el(sel, root) { return (root || S.root).querySelector(sel); }
  function all(sel, root) { return [...(root || S.root).querySelectorAll(sel)]; }

  function build() {
    const root = document.createElement("aside");
    root.id = "avatarStage";
    root.className = "av";
    root.dataset.state = "idle";
    root.dataset.mode = "art";
    root.dataset.open = "false";
    root.dataset.expanded = "false";
    root.dataset.hidden = "false";
    root.setAttribute("aria-label", tr("video"));
    root.innerHTML = TPL;
    document.body.appendChild(root);
    S.root = root;
    S.els = {
      screen: el(".av-screen"), card: el(".av-card"), orb: el(".av-orb"),
      vidA: el('[data-slot="a"]'), vidB: el('[data-slot="b"]'),
      name: el(".av-name"), role: el(".av-role"), status: el(".av-status .t"),
      track: el(".av-track"), fill: el(".av-fill"), knob: el(".av-knob"), time: el(".av-time"),
      play: el('[data-av="play"]'), mute: el('[data-av="mute"]'),
      pin: el('[data-av="pin"]'), full: el('[data-av="full"]'),
      eq: all(".av-eq i"),
    };
  }

  /* ------------------------------------------------------------------ الترجمة */
  function applyLabels() {
    if (!S.root) return;
    const b = S.els;
    const name = S.agent && S.agent.name ? S.agent.name : tr("name");
    const role = S.agent && S.agent.role ? S.agent.role : tr("role");
    b.name.textContent = name;
    b.role.textContent = role;
    b.status.textContent = tr(S.state === "idle" ? "ready" : S.state);
    S.root.setAttribute("aria-label", tr("video"));
    b.card.setAttribute("aria-label", name + " — " + role);
    b.play.setAttribute("aria-label", b.play.dataset.playing === "1" ? tr("pause") : tr("play"));
    b.play.setAttribute("title", b.play.getAttribute("aria-label"));
    b.mute.setAttribute("aria-label", S.muted ? tr("unmute") : tr("mute"));
    b.mute.setAttribute("title", b.mute.getAttribute("aria-label"));
    el('[data-av="replay"]').setAttribute("title", tr("replay"));
    el('[data-av="replay"]').setAttribute("aria-label", tr("replay"));
    b.full.setAttribute("aria-label", document.fullscreenElement ? tr("exitFull") : tr("full"));
    b.full.setAttribute("title", b.full.getAttribute("aria-label"));
    el('[data-av="pin"]').setAttribute("aria-label", S.pinned ? tr("unpin") : tr("pin"));
    el('[data-av="pin"]').setAttribute("title", el('[data-av="pin"]').getAttribute("aria-label"));
    el('[data-av="min"]').setAttribute("aria-label", tr("collapse"));
    el('[data-av="min"]').setAttribute("title", tr("collapse"));
    b.orb.setAttribute("aria-label", tr("open"));
    b.orb.setAttribute("title", tr("open"));
    b.track.setAttribute("aria-label", tr("seek"));
    const zoomBtn = el('[data-av="zoom"]');
    zoomBtn.setAttribute("aria-label", tr("zoom"));
    zoomBtn.setAttribute("title", tr("zoom"));
    b.pin.classList.toggle("on", S.pinned);
    b.pin.setAttribute("aria-pressed", String(S.pinned));
    const tb = document.getElementById("avatarBtn");
    if (tb) tb.setAttribute("aria-pressed", String(!!S.open && !S.hidden));
  }

  /* ------------------------------------------------------------------ الفيديو */
  const probeCache = new Map();
  async function probe(url) {
    if (probeCache.has(url)) return probeCache.get(url);
    let ok = false;
    try {
      const r = await fetch(url, { method: "HEAD" });
      const ct = (r.headers.get("content-type") || "").toLowerCase();
      ok = r.ok && ct.startsWith("video");
    } catch { ok = false; }
    probeCache.set(url, ok);
    return ok;
  }
  async function firstAvailable(list) {
    for (const u of list) { if (await probe(u)) return u; }
    return null;
  }

  async function discover() {
    const [idle, talk] = await Promise.all([firstAvailable(CLIPS.idle), firstAvailable(CLIPS.talk)]);
    S.clips = { idle, talk: talk || idle };
    if (!idle) { S.mode = "art"; S.root.dataset.mode = "art"; applyLabels(); return; }
    S.mode = "video";
    S.root.dataset.mode = "video";
    S.els.vidA.src = idle;
    S.els.vidA.classList.add("on");
    if (S.clips.talk && S.clips.talk !== idle) S.els.vidB.src = S.clips.talk;
    S.els.vidA.play().catch(() => {});
    if (S.els.vidB.src) S.els.vidB.play().catch(() => {});
    applyMute();
    applyLabels();
  }

  function activeVideo() { return S.active === "b" && S.els.vidB.src ? S.els.vidB : S.els.vidA; }

  function setClip(kind) {
    if (S.mode !== "video") return;
    const want = kind === "talk" && S.els.vidB.src ? "b" : "a";
    if (want === S.active) return;
    const from = activeVideo();
    const to = want === "b" ? S.els.vidB : S.els.vidA;
    to.currentTime = 0;
    to.play().catch(() => {});
    from.classList.remove("on");
    to.classList.add("on");
    S.active = want;
    applyMute();
    if (from !== to) setTimeout(() => { if (S.active !== (from === S.els.vidB ? "b" : "a")) from.pause(); }, 340);
  }

  function applyMute() {
    const a = S.els.vidA, b = S.els.vidB;
    a.muted = S.muted || S.active !== "a";
    b.muted = S.muted || S.active !== "b";
    S.els.mute.querySelector("use").setAttribute("href", S.muted ? "#i-speaker" : "#i-mute");
    S.els.mute.classList.toggle("on", !S.muted);
    S.els.mute.setAttribute("aria-label", S.muted ? tr("unmute") : tr("mute"));
    S.els.mute.setAttribute("title", S.els.mute.getAttribute("aria-label"));
  }

  function setPlaying(playing) {
    const v = activeVideo();
    if (!v) return;
    if (playing) v.play().catch(() => setPlaying(false));
    else v.pause();
    S.els.play.dataset.playing = playing ? "1" : "0";
    if (S.root) S.root.dataset.playing = playing ? "1" : "0";
    S.els.play.querySelector("use").setAttribute("href", playing ? "#i-pause" : "#i-play");
    S.els.play.setAttribute("aria-label", playing ? tr("pause") : tr("play"));
    S.els.play.setAttribute("title", S.els.play.getAttribute("aria-label"));
  }

  function tick() {
    if (S.mode !== "video") return;
    const v = activeVideo();
    if (v && v.duration && isFinite(v.duration)) {
      const pct = Math.min(100, (v.currentTime / v.duration) * 100);
      S.els.fill.style.width = pct + "%";
      S.els.knob.style.insetInlineStart = pct + "%";
      S.els.track.setAttribute("aria-valuenow", String(Math.round(pct)));
      S.els.track.setAttribute("aria-valuetext", fmt(v.currentTime) + " / " + fmt(v.duration));
      S.els.time.textContent = fmt(v.currentTime);
      const playing = !v.paused;
      if (S.els.play.dataset.playing !== (playing ? "1" : "0")) setPlaying(playing);
    }
  }
  function fmt(t) {
    if (!isFinite(t)) return "0:00";
    const m = Math.floor(t / 60), s = Math.floor(t % 60);
    return m + ":" + String(s).padStart(2, "0");
  }

  /* ------------------------------------------------------------------ الحالة */
  function setState(next) {
    if (!S.root) return;
    const allowed = ["idle", "listening", "thinking", "speaking", "error"];
    const st = allowed.includes(next) ? next : "idle";
    const changed = st !== S.state;
    S.state = st;
    S.root.dataset.state = st;
    S.els.status.textContent = tr(st === "idle" ? "ready" : st);
    setClip(st === "speaking" ? "talk" : "idle");

    if (st === "speaking" || st === "listening" || st === "thinking") {
      clearTimeout(S.collapseTimer);
      wake();
    }
    if (st === "idle" && changed) scheduleCollapse();
    document.dispatchEvent(new CustomEvent("avatarstate", { detail: { state: st } }));
  }

  function setAgent(a) {
    S.agent = a && a.name ? { name: a.name, role: a.role || "" } : null;
    applyLabels();
  }

  /* ------------------------------------------------------------------ الفتح */
  function open(pin) {
    clearTimeout(S.collapseTimer);
    S.open = true;
    S.root.dataset.open = "true";
    if (pin) { S.pinned = true; store.set(LS.pinned, "1"); }
    applyLabels();
    if (S.mode === "video") activeVideo().play().catch(() => {});
    if (S.els.card) S.els.card.style.animation = "none", requestAnimationFrame(() => { S.els.card.style.animation = ""; });
  }
  function collapse() {
    if (!S.root) return;
    S.open = false;
    S.root.dataset.open = "false";
    applyLabels();
  }
  function scheduleCollapse() {
    clearTimeout(S.collapseTimer);
    if (S.pinned) return;
    S.collapseTimer = setTimeout(() => { if (S.state === "idle") collapse(); }, 4200);
  }
  function wake() {
    if (!S.root || S.hidden) return;
    if (!S.open) open(false);
  }
  function show() {
    S.hidden = false;
    S.root.dataset.hidden = "false";
    store.set(LS.hidden, "0");
    open(true);
  }
  function hide() {
    S.hidden = true;
    S.root.dataset.hidden = "true";
    store.set(LS.hidden, "1");
  }
  function toggle() {
    if (S.hidden) return show();
    if (S.open) { S.pinned = false; store.set(LS.pinned, "0"); collapse(); }
    else open(true);
  }

  /* ------------------------------------------------------------------ الصوت */
  function audioCtx() {
    if (!S.audioCtx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      S.audioCtx = new AC();
    }
    if (S.audioCtx.state === "suspended") S.audioCtx.resume().catch(() => {});
    return S.audioCtx;
  }

  function bindAudio(mediaEl) {
    if (!mediaEl) return;
    try {
      const ctx = audioCtx();
      if (!ctx) return;
      S.srcNode = ctx.createMediaElementSource(mediaEl);
      S.analyser = ctx.createAnalyser();
      S.analyser.fftSize = 1024;
      S.analyser.smoothingTimeConstant = 0.72;
      S.srcNode.connect(S.analyser);
      S.analyser.connect(ctx.destination);
      S.freq = new Uint8Array(S.analyser.fftSize);
      S.root.dataset.audio = "1";
      setState("speaking");
      if (!S.audioRaf) audioRaf();
    } catch {
      /* المتصفح رفض التحليل — نكمل بحركة الفم الافتراضية */
      unbindAudio();
      setState("speaking");
    }
  }

  function audioRaf() {
    S.audioRaf = requestAnimationFrame(audioRaf);
    if (!S.analyser || !S.freq) return;
    S.analyser.getByteTimeDomainData(S.freq);
    let sum = 0;
    for (let i = 0; i < S.freq.length; i++) { const v = (S.freq[i] - 128) / 128; sum += v * v; }
    const rms = Math.sqrt(sum / S.freq.length);
    const level = Math.max(0, Math.min(1, rms * 7.5));
    S.root.style.setProperty("--av-mouth", level.toFixed(3));
    S.els.eq.forEach((bar, i) => {
      const f = [1, 1.35, 1.7, 1.25, .9][i] || 1;
      bar.style.transform = "scaleY(" + Math.max(0.14, Math.min(1, level * f * 1.6)).toFixed(3) + ")";
    });
  }

  function unbindAudio() {
    cancelAnimationFrame(S.audioRaf);
    S.audioRaf = 0;
    try { S.srcNode && S.srcNode.disconnect(); } catch {}
    try { S.analyser && S.analyser.disconnect(); } catch {}
    S.srcNode = null; S.analyser = null; S.freq = null;
    if (S.root) {
      delete S.root.dataset.audio;
      S.root.style.removeProperty("--av-mouth");
      S.els.eq.forEach((b) => { b.style.transform = ""; });
    }
  }

  /* ------------------------------------------------------------------ الأحداث */
  function bindUI() {
    S.root.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-av]");
      if (!btn) {
        // على الموبايل: لمس الفقاعة الصغيرة يوسّعها
        if (window.matchMedia("(max-width: 520px)").matches && S.open &&
            S.root.dataset.expanded === "false" && e.target.closest(".av-screen")) {
          S.root.dataset.expanded = "true";
        }
        return;
      }
      const act = btn.dataset.av;
      if (act === "open") return open(true);
      if (act === "zoom") {
        S.root.dataset.expanded = S.root.dataset.expanded === "true" ? "false" : "true";
        return;
      }
      if (act === "min") { S.pinned = false; store.set(LS.pinned, "0"); S.root.dataset.expanded = "false"; return collapse(); }
      if (act === "pin") {
        S.pinned = !S.pinned;
        store.set(LS.pinned, S.pinned ? "1" : "0");
        applyLabels();
        if (S.pinned) open(true); else scheduleCollapse();
        return;
      }
      if (act === "close") return hide();
      if (act === "play") return setPlaying(S.els.play.dataset.playing !== "1");
      if (act === "replay") {
        const v = activeVideo();
        if (v) { v.currentTime = 0; v.play().catch(() => {}); setPlaying(true); }
        return;
      }
      if (act === "mute") {
        S.muted = !S.muted;
        store.set(LS.muted, S.muted ? "1" : "0");
        applyMute();
        return;
      }
      if (act === "full") {
        try {
          if (document.fullscreenElement) await document.exitFullscreen();
          else await S.els.screen.requestFullscreen();
        } catch {}
        return;
      }
    });

    // السحب على شريط التقدم + النقر للانتقال
    let dragging = false;
    const seek = (clientX) => {
      const v = activeVideo();
      const r = S.els.track.getBoundingClientRect();
      if (!v || !v.duration || !r.width) return;
      let ratio = (clientX - r.left) / r.width;
      if (document.documentElement.dir === "rtl") ratio = 1 - ratio;
      v.currentTime = Math.max(0, Math.min(1, ratio)) * v.duration;
      tick();
    };
    S.els.track.addEventListener("pointerdown", (e) => {
      if (S.mode !== "video") return;
      dragging = true;
      S.els.track.setPointerCapture?.(e.pointerId);
      seek(e.clientX);
    });
    S.els.track.addEventListener("pointermove", (e) => { if (dragging) seek(e.clientX); });
    S.els.track.addEventListener("pointerup", () => { dragging = false; });
    S.els.track.addEventListener("pointercancel", () => { dragging = false; });
    S.els.track.addEventListener("keydown", (e) => {
      const v = activeVideo();
      if (!v) return;
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        e.preventDefault();
        const dir = document.documentElement.dir === "rtl" ? -1 : 1;
        const step = (e.key === "ArrowRight" ? 1 : -1) * dir * 1;
        v.currentTime = Math.max(0, Math.min(v.duration || 0, v.currentTime + step));
        tick();
      }
      if (e.key === " " || e.key === "Enter") { e.preventDefault(); setPlaying(v.paused); }
    });

    [S.els.vidA, S.els.vidB].forEach((v) => {
      v.addEventListener("timeupdate", () => { if (v === activeVideo()) tick(); });
      v.addEventListener("loadedmetadata", () => { if (v === activeVideo()) tick(); });
      v.addEventListener("error", () => {
        // فشل تحميل الفيديو → ارجع للرسم المتحرك بدل شاشة سوداء
        if (v === S.els.vidA) { S.mode = "art"; S.root.dataset.mode = "art"; applyLabels(); }
      });
    });

    document.addEventListener("fullscreenchange", () => {
      applyLabels();
      if (!document.fullscreenElement) tick();
    });
    document.addEventListener("langchange", () => applyLabels());

    // إيقاف الحركة عند إخفاء التبويب (توفير بطارية/معالجة)
    document.addEventListener("visibilitychange", () => {
      const v = activeVideo();
      if (!v) return;
      if (document.hidden) v.pause();
      else if (S.open) v.play().catch(() => {});
    });

    window.addEventListener("resize", () => { if (S.open) tick(); });
  }

  function mount() {
    if (S.root) return;
    build();
    bindUI();
    // رابط عرض تجريبي: /?avatar=1 يفتح المساعد، و ?avatar=speaking يفتحه في حالة الكلام
    try {
      const q = new URLSearchParams(location.search).get("avatar");
      if (q) {
        S.root.dataset.hidden = "false";
        setTimeout(() => { open(true); if (q === "speaking" || q === "thinking" || q === "listening") setState(q); }, 350);
      }
    } catch {}
    S.hidden = store.get(LS.hidden, "0") === "1";
    S.root.dataset.hidden = S.hidden ? "true" : "false";
    S.pinned = store.get(LS.pinned, "0") === "1";
    S.muted = store.get(LS.muted, "1") !== "0";
    applyLabels();
    applyMute();
    if (S.hidden) { /* يظل مخفياً حتى يطلبه المستخدم */ }
    discover();
  }

  window.AvatarStage = {
    mount,
    setState,
    setAgent,
    bindAudio,
    unbindAudio,
    open: () => open(true),
    collapse,
    show,
    hide,
    toggle,
    wake,
    isOpen: () => !!S.open,
    _state: () => S.state,
  };

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
