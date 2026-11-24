@echo off
chcp 65001 >nul
title فريق الوكلاء الأكاديمي - AI MAS Hub
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [X] Python غير مثبت — ثبّته من python.org مع تفعيل خيار Add to PATH ثم أعد المحاولة
  pause
  exit /b 1
)
echo [*] التأكد من المكتبات (أول مرة فقط قد تأخذ دقائق)...
python -m pip install -q --disable-pip-version-check -r requirements.txt
echo [*] تشغيل الخادم... سيفتح المتصفح تلقائياً على http://localhost:8765
python app.py
pause
