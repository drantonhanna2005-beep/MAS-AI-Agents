@echo off
chcp 65001 >nul
title تدريب الفريق على درويفات جوجل
cd /d "%~dp0"
echo [*] هذا السكربت ينزّل مجلدات الدرويف المرتبطة داخل data\ ثم يبني الفهرس
python -m pip install -q --disable-pip-version-check -r requirements.txt
python ingest.py --download
echo.
echo [✓] تم — شغّل run.bat واستمتع بفريق مدرّب على ملفاتك
pause
