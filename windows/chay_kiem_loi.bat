@echo off
title Tom's Jukebox - Kiem Loi
cd /d "%~dp0"
echo Mo Tom's Jukebox kem cua so den nay de xem loi. Dong cua so nay se dong chuong trinh.
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
echo.
echo Chuong trinh da dong. Log: %APPDATA%\Tom's Jukebox\TomsJukebox.log
pause
