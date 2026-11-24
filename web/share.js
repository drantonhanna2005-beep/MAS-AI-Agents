"use strict";
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleString(undefined, { year:"numeric", month:"short", day:"2-digit", hour:"2-digit", minute:"2-digit" });
}
function inlineMd(s) {
  s = esc(s);
  s = s.replace(/`([^`]+)`/g, (_m, c) => `<code>${c}</code>`);
  s = s.replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  s = s.replace(/\*([^*\n]+)\*/g, "<em>$1</em>");
  const safeUrl = (u) => u.replace(/"/g, "%22").replace(/'/g, "%27");
  s = s.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, (_m, tt, u) => `<a href="${safeUrl(u)}" target="_blank" rel="noopener">${tt}</a>`);
  s = s.replace(/(^|[\s>])(https?:\/\/[^\s<]+)/g, (_m, p, u) => `${p}<a href="${safeUrl(u)}" target="_blank" rel="noopener">${u}</a>`);
  return s;
}
function md(src) {
  const blocks = [];
  src = String(src ?? "").replace(/```([\w+-]*)\n?([\s\S]*?)```/g, (_m, lang, code) => {
    const safeLang = esc((lang || "").trim());
    const body = esc(code.replace(/\n$/, ""));
    blocks.push(`<div class="code-block" dir="ltr"><div class="code-head"><span>${safeLang || "code"}</span><span class="code-actions"><button class="code-copy" data-copy-code title="Copy">⧉ Copy</button><button class="code-full" data-full-code title="Full screen">⛶</button></span></div><pre><code class="${safeLang ? `language-${safeLang}` : ""}">${body}</code></pre></div>`);
    return "\u0000" + (blocks.length - 1) + "\u0000";
  });
  const out = [];
  let ul = null, ol = null, table = [];
  const flushLists = () => { if (ul) { out.push("<ul>" + ul.join("") + "</ul>"); ul = null; } if (ol) { out.push("<ol>" + ol.join("") + "</ol>"); ol = null; } };
  const flushTable = () => {
    if (!table.length) return;
    const rows = table.filter((r) => !/^[\s|:\-]+$/.test(r));
    const cells = (r) => r.replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => inlineMd(c.trim()));
    let html = "<div class='table-wrap'><table>";
    rows.forEach((r, ri) => { const tag = ri === 0 ? "th" : "td"; html += "<tr>" + cells(r).map((c) => `<${tag}>${c}</${tag}>`).join("") + "</tr>"; });
    out.push(html + "</table></div>"); table = [];
  };
  for (const line of src.split("\n")) {
    if (/^\s*\|.*\|\s*$/.test(line)) { flushLists(); table.push(line.trim()); continue; }
    flushTable();
    const h = line.match(/^(#{1,6})\s+(.*)/);
    if (h) { flushLists(); const lvl=Math.min(4,h[1].length+1); out.push(`<h${lvl}>${inlineMd(h[2])}</h${lvl}>`); continue; }
    if (/^\s*[-*•]\s+/.test(line)) { if (ol) { out.push("<ol>" + ol.join("") + "</ol>"); ol = null; } (ul ??= []).push("<li>" + inlineMd(line.replace(/^\s*[-*•]\s+/, "")) + "</li>"); continue; }
    if (/^\s*\d+[.)]\s+/.test(line)) { if (ul) { out.push("<ul>" + ul.join("") + "</ul>"); ul = null; } (ol ??= []).push("<li>" + inlineMd(line.replace(/^\s*\d+[.)]\s+/, "")) + "</li>"); continue; }
    if (/^\s*>\s?/.test(line)) { flushLists(); out.push("<blockquote>" + inlineMd(line.replace(/^\s*>\s?/, "")) + "</blockquote>"); continue; }
    if (/^\s*([-*_]\s*){3,}$/.test(line)) { flushLists(); out.push("<hr>"); continue; }
    if (!line.trim()) { flushLists(); continue; }
    flushLists();
    out.push("<p>" + inlineMd(line) + "</p>");
  }
  flushLists(); flushTable();
  return out.join("").replace(/\u0000(\d+)\u0000/g, (_m, i) => blocks[+i] ?? "");
}
function attachmentURL(a) {
  if (a.library_id) return `/api/library/${encodeURIComponent(a.library_id)}/file`;
  if (a.dataUrl) return a.dataUrl;
  return "";
}
function renderAttachments(atts=[]) {
  const items = (atts||[]).filter(a => a && (a.name || a.library_id || a.dataUrl));
  if (!items.length) return "";
  return `<div class="share-atts">${items.map(a => {
    const url = attachmentURL(a);
    const name = esc(a.name || 'attachment');
    const isImg = (a.kind==='image') || /^image\//.test(a.mime||a.type||'') || /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(a.name||'');
    if (isImg && url) {
      return `<figure class="share-att img"><img src="${esc(url)}" alt="${name}" loading="lazy" class="share-img" data-full="${esc(url)}"><figcaption><span>${name}</span>${url?`<a href="${esc(url)}" download="${name}">Download</a>`:''}</figcaption></figure>`;
    }
    if (url) return `<div class="share-att file"><span>${name}</span><a href="${esc(url)}" download="${name}">Download</a></div>`;
    return `<div class="share-att file"><span>${name}</span></div>`;
  }).join("")}</div>`;
}
function showLightbox(src, name='') {
  let lb = document.querySelector('.share-lightbox');
  if (!lb) {
    lb = document.createElement('div');
    lb.className = 'share-lightbox';
    lb.innerHTML = `<div class="share-lightbox-inner"><button class="share-lightbox-close" aria-label="Close">×</button><img alt=""><div class="share-lightbox-cap"></div></div>`;
    document.body.appendChild(lb);
    lb.addEventListener('click', (e)=>{ if (e.target === lb || e.target.closest('.share-lightbox-close')) lb.classList.remove('open'); });
    document.addEventListener('keydown', (e)=>{ if (e.key === 'Escape') lb.classList.remove('open'); });
  }
  lb.querySelector('img').src = src;
  lb.querySelector('.share-lightbox-cap').textContent = name || '';
  lb.classList.add('open');
}

async function init() {
  const sid = location.pathname.split("/").filter(Boolean).pop();
  if (!sid) { document.body.textContent = "Not found"; return; }
  try {
    const res = await fetch("/api/share/" + encodeURIComponent(sid));
    const d = await res.json();
    if (!res.ok || d.error) throw new Error(d.error || "Not found");
    const theme = (d.theme === 'light' || d.theme === 'dark') ? d.theme : 'dark';
    document.documentElement.dataset.theme = theme;
    document.documentElement.style.colorScheme = theme;
    document.body.dataset.theme = theme;
    const title = d.title || "Shared conversation";
    document.getElementById("shareTitle").textContent = title;
    const when = fmtTime(d.shared_at || d.created);
    document.getElementById("shareMeta").textContent = `${d.count || (d.messages||[]).length} messages • ${when}`;
    document.title = title + " — MAS AI Agents";
    const msgs = document.getElementById("shareMsgs");
    msgs.innerHTML = (d.messages || []).map((m) => {
      const who = m.role === "user" ? "You" : (m.agent || "Assistant");
      const whenStr = fmtTime(m.created);
      const edited = m.edited_at ? ` <span class="edited">(edited ${esc(fmtTime(m.edited_at))})</span>` : "";
      return `<article class="share-msg ${m.role === "user" ? "user" : "ai"}">
        <div class="meta"><span class="who">${esc(who)}</span><span class="time">${esc(whenStr)}${edited}</span></div>
        <div class="body md">${md(m.content || "")}</div>
        ${renderAttachments(m.attachments || [])}
        ${m.thinking ? `<details class="share-think"><summary>Deep thinking</summary><div class="think-body">${esc(m.thinking)}</div></details>` : ""}
      </article>`;
    }).join("");
  } catch (e) {
    document.getElementById("shareTitle").textContent = "Link not found";
    document.getElementById("shareMsgs").innerHTML = `<div class="share-msg"><div class="body">This shared conversation is unavailable or has been removed.</div></div>`;
  }

  document.addEventListener('click', async (e) => {
    const copyBtn = e.target.closest('[data-copy-code]');
    if (copyBtn) {
      const pre = copyBtn.closest('.code-block')?.querySelector('pre') || copyBtn.closest('.code-full-card')?.querySelector('pre');
      const text = pre?.innerText || '';
      try { await navigator.clipboard.writeText(text); copyBtn.textContent='Copied'; setTimeout(()=>copyBtn.textContent='Copy', 1200); } catch {}
      return;
    }
    const img = e.target.closest('.share-img');
    if (img) { showLightbox(img.dataset.full || img.src, img.alt || ''); return; }
    const fullBtn = e.target.closest('[data-full-code]');
    if (fullBtn) {
      const blk = fullBtn.closest('.code-block');
      const code = blk?.querySelector('pre')?.innerText || '';
      const lang = blk?.querySelector('.code-head span')?.textContent || 'code';
      let fm = document.querySelector('.code-full-modal');
      if (!fm) {
        fm = document.createElement('div'); fm.className = 'code-full-modal';
        fm.innerHTML = `<div class="code-full-card" dir="ltr"><div class="code-head"><span class="cf-lang"></span><span class="code-actions"><button class="code-copy" data-copy-code>⧉ Copy</button><button class="code-close" title="Close">✕</button></span></div><pre class="cf-pre"><code></code></pre></div>`;
        document.body.appendChild(fm);
        fm.addEventListener('click', (ev) => { if (ev.target === fm || ev.target.closest('.code-close')) fm.classList.remove('open'); });
        document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') fm.classList.remove('open'); });
      }
      fm.querySelector('.cf-lang').textContent = lang;
      fm.querySelector('pre code').textContent = code;
      fm.classList.add('open');
      return;
    }
  });

  const copyLink = document.getElementById("copyLink");
  copyLink?.addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(location.href); }
    catch { const i = document.createElement("input"); i.value = location.href; document.body.appendChild(i); i.select(); document.execCommand("copy"); i.remove(); }
    copyLink.textContent = "Copied ✓";
    setTimeout(() => (copyLink.textContent = "Copy link"), 1800);
  });
}
init();
