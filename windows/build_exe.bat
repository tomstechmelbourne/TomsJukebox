@echo off
setlocal
title Tom's Jukebox - Dong Goi TomsJukebox.exe
cd /d "%~dp0"
set "TJ_DIR=%~dp0"
if not exist ".venv\Scripts\python.exe" goto not_installed
set "VPY=%TJ_DIR%.venv\Scripts\python.exe"
echo [1/3] Cai PyInstaller ...
"%VPY%" -m pip install pyinstaller --timeout 180 --retries 10 -q
echo [2/3] Dang dong goi TomsJukebox.exe, khoang 2-5 phut ...
"%VPY%" -m PyInstaller --noconfirm --clean --windowed --name TomsJukebox --icon assets\app_icon.ico --version-file version_info.txt --add-data "assets;assets" --collect-all av --collect-all sounddevice --collect-submodules scipy.signal --collect-submodules winrt --hidden-import comtypes.client --hidden-import tomsjukebox.selftest --hidden-import tomsjukebox.demo --collect-submodules tomsjukebox main.py
if errorlevel 1 goto build_fail
echo [3/3] Tu kiem tra ban .exe: --demo --selftest ...
start /wait "" "dist\TomsJukebox\TomsJukebox.exe" --demo --selftest
if errorlevel 1 echo  TU KIEM TRA: CO LOI - xem TomsJukebox.log trong thu muc %%APPDATA%%\Tom's Jukebox
if not errorlevel 1 echo  TU KIEM TRA: DAT
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=$env:TJ_DIR+'dist\TomsJukebox\'; $s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Tom''s Jukebox.lnk'); $s.TargetPath=$d+'TomsJukebox.exe'; $s.WorkingDirectory=$d; $s.IconLocation=$d+'TomsJukebox.exe'; $s.Save()"
echo.
echo Xong. File chay: dist\TomsJukebox\TomsJukebox.exe - loi tat ngoai Desktop da tro toi file nay.
pause
exit /b 0

:not_installed
echo Chua cai dat. Chay cai_dat.bat truoc.
pause
exit /b 1

:build_fail
echo Loi khi dong goi.
pause
exit /b 1
