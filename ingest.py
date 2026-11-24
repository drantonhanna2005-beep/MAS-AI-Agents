"""أداة التدريب والفهرسة — تُدرّب الفريق على ملفاتك.

الاستخدام:
    python ingest.py               فهرسة كل ما في مجلد data/ (+ قاعدة المعرفة)
    python ingest.py --download    تنزيل درويفات جوجل المرتبطة أولاً ثم الفهرسة
    python ingest.py --download-only  تنزيل فقط بدون فهرسة
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from core import rag
from core.config import DATA_DIR
from core.knowledge import DRIVE_LINKS


def download_drives() -> int:
    try:
        import gdown
    except ImportError:
        print("✗ مكتبة gdown غير مثبتة — نفّذ: pip install gdown")
        return 0
    ok = 0
    for link in DRIVE_LINKS:
        url = link["url"]
        if "/folders/" not in url:
            continue
        name = link["name"].replace(" ", "_").replace("—", "-")[:40]
        out = DATA_DIR / name
        if out.exists() and any(out.iterdir()):
            print(f"✓ منزّل مسبقاً: {name}")
            ok += 1
            continue
        print(f"⬇ تنزيل: {link['name']} …")
        try:
            gdown.download_folder(url=url, output=str(out), quiet=False, use_cookies=False, remaining_ok=True)
            ok += 1
        except Exception as e:
            print(f"✗ فشل تنزيل «{name}»: {e}\n  (جرّب يدوياً من المتصفح وضع الملفات في data/{name})")
    return ok


def main() -> None:
    ap = argparse.ArgumentParser(description="تدريب الفريق على ملفاتك")
    ap.add_argument("--download", action="store_true", help="تنزيل الدرويفات من جوجل درايف")
    ap.add_argument("--download-only", action="store_true", help="تنزيل فقط بدون إعادة فهرسة")
    args = ap.parse_args()

    if args.download or args.download_only:
        n = download_drives()
        print(f"\nتم تنزيل/تأكيد {n} مجلد درايف → داخل {DATA_DIR}")

    if args.download_only:
        return

    print("🔄 جاري بناء الفهرس من:", DATA_DIR)
    res = rag.build_index()
    if res.get("busy"):
        print("⏳ هناك فهرسة جارية بالفعل — انتظر قليلاً ثم أعد المحاولة.")
        return
    print(f"✅ تم: {res['files']} ملف → {res['chunks']} مقطع معرفة "
          f"({'بحث دلالي مفعّل' if res.get('semantic') else 'بحث بالكلمات (ثبّت Ollama لتفعيل الدلالي)'})")


if __name__ == "__main__":
    main()
