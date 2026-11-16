@echo off
setlocal EnableDelayedExpansion
title Tom's Jukebox - Cai Dat
cd /d "%~dp0"
set "TJ_DIR=%~dp0"
echo.
echo  ==========================================================
echo    TOM'S JUKEBOX 0.9.6-beta  -  Cai dat, chi can chay 1 lan
echo    One of Tom's Technology Solutions Products
echo  ==========================================================
echo.

rem ---------- [1/4] Tim Python 3.12 hoac 3.11
set "PYEXE="
for %%V in (3.12 3.11) do (
    if not defined PYEXE (
        for /f "usebackq delims=" %%E in (`py -%%V -c "import sys;print(sys.executable)" 2^>nul`) do set "PYEXE=%%E"
    )
)
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYEXE if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
if defined PYEXE goto have_python

echo [1/4] Chua co Python 3.12 - dang tai ve tu python.org ...
curl.exe -L --retry 5 --retry-delay 3 -o "%TEMP%\python-3.12-installer.exe" "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
if errorlevel 1 goto python_fail
echo      Dang cai Python 3.12, khoang 1-2 phut ...
"%TEMP%\python-3.12-installer.exe" /quiet InstallAllUsers=0 PrependPath=0 Include_launcher=1 Include_test=0
set "PYEXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PYEXE%" goto python_fail

:have_python
echo [1/4] Python: %PYEXE%

rem ---------- [2/4] Moi truong rieng .venv
if exist ".venv\Scripts\python.exe" goto have_venv
echo [2/4] Dang tao moi truong .venv ...
"%PYEXE%" -m venv .venv
if errorlevel 1 goto venv_fail
goto venv_done
:have_venv
echo [2/4] Da co .venv - dung lai.
:venv_done
set "VPY=%TJ_DIR%.venv\Scripts\python.exe"

rem ---------- [3/4] Thu vien, thu lai toi da 3 lan khi mang cham
echo [3/4] Dang cai thu vien: PySide6, PyAV/FFmpeg, mutagen, numpy, scipy, sounddevice, Pillow
echo      Lan dau co the mat 3-10 phut tuy toc do mang. Xin cho...
"%VPY%" -m pip install --upgrade pip --timeout 120 --retries 10 -q
set /a TRY=0
:pip_again
set /a TRY+=1
"%VPY%" -m pip install -r requirements.txt --timeout 180 --retries 10 --progress-bar off
if not errorlevel 1 goto pip_ok
if !TRY! GEQ 3 goto pip_fail
echo      Mang bi ngat - thu lai lan !TRY! ...
goto pip_again
:pip_ok
echo      Them phan rieng cho Windows: phim media, nut tren taskbar, vi tri ...
"%VPY%" -m pip install -r requirements-windows.txt --timeout 180 --retries 10 --progress-bar off
if errorlevel 1 echo      Phan rieng cho Windows chua cai duoc - chuong trinh van chay binh thuong.

rem ---------- [4/4] Loi tat ngoai Desktop, mo bang pythonw nen khong co cua so den
echo [4/4] Tao loi tat Tom's Jukebox ngoai Desktop ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$d=$env:TJ_DIR; $s=(New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Tom''s Jukebox.lnk'); $s.TargetPath=$d+'.venv\Scripts\pythonw.exe'; $s.Arguments='\"'+$d+'main.py\"'; $s.WorkingDirectory=$d; $s.IconLocation=$d+'assets\app_icon.ico'; $s.Description='Tom''s Jukebox'; $s.Save()"

echo.
echo  Xong! Mo chuong trinh bang loi tat "Tom's Jukebox" ngoai Desktop, hoac chay chay.bat
echo  chay_demo.bat = nhac mau de thu.   chay_kiem_loi.bat = mo kem cua so den de tim loi.
echo.
pause
exit /b 0

:python_fail
echo.
echo  Khong tai hoac cai duoc Python. Tom kiem tra mang roi chay lai cai_dat.bat.
echo  Hoac tu cai Python 3.12 tu https://www.python.org/downloads/
pause
exit /b 1

:venv_fail
echo  Loi khi tao .venv
pause
exit /b 1

:pip_fail
echo.
echo  Chua cai xong thu vien. Tom chay lai cai_dat.bat, chuong trinh se cai tiep phan con thieu.
pause
exit /b 1
