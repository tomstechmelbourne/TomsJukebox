#!/bin/bash
# Emulator smoke test: install, start, look around, check that the app is still alive, take screenshots.
set -x
API=$1
APK=$(ls app/build/outputs/apk/release/*.apk | head -1)
mkdir -p shots
# wait until Android has really settled (new system images restart system_server once after boot)
adb wait-for-device
for i in $(seq 1 60); do [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1" ] && break; sleep 5; done
sleep 45
ok=0
for i in 1 2 3; do
  adb wait-for-device
  until adb shell pm path android >/dev/null 2>&1; do sleep 5; done
  if adb install -r -g "$APK" 2>&1 | grep -q Success; then ok=1; break; fi
  echo "install try $i failed, waiting"; sleep 40
done
[ $ok = 1 ] || { echo "INSTALL FAILED (emulator)"; exit 1; }
adb shell pm grant com.tomstechsolutions.jukebox android.permission.POST_NOTIFICATIONS 2>/dev/null
adb logcat -c
adb shell am start -W -n com.tomstechsolutions.jukebox/.ui.MainActivity
sleep 8
adb exec-out screencap -p > shots/api${API}_1_library.png
# bottom nav taps (pages) using keyboard shortcuts 2..5
for k in 9 10 11 12; do adb shell input keyevent $k; sleep 3; adb exec-out screencap -p > shots/api${API}_page_$k.png; done
adb shell input keyevent 8; sleep 2
# open Now Playing with L (lyrics) then back
adb shell input keyevent 40; sleep 3; adb exec-out screencap -p > shots/api${API}_now.png
adb shell input keyevent 111; sleep 2
# rotate to landscape
adb shell settings put system accelerometer_rotation 0
adb shell settings put system user_rotation 1; sleep 4
adb exec-out screencap -p > shots/api${API}_landscape.png
adb shell settings put system user_rotation 0; sleep 3
# 0.9.3 pages: theme pack picker, visualisation picker, a theme pack applied, full-screen flag visualisation, podcast page
M=com.tomstechsolutions.jukebox/.ui.MainActivity
adb shell am start -n $M --es open_picker pack; sleep 4; adb exec-out screencap -p > shots/api${API}_picker_pack.png
adb shell input keyevent 4; sleep 2
adb shell am start -n $M --es open_picker viz; sleep 4; adb exec-out screencap -p > shots/api${API}_picker_viz.png
adb shell input keyevent 4; sleep 2
adb shell am start -n $M --ei apply_pack 55 --es open_tab 0; sleep 4; adb exec-out screencap -p > shots/api${API}_pack55.png
adb shell am start -n $M --ei set_viz 70 --ez full_viz true; sleep 4; adb exec-out screencap -p > shots/api${API}_viz70.png
adb shell input keyevent 4; sleep 2
adb shell am start -n $M --ei apply_pack 52 --es open_tab 2; sleep 12; adb exec-out screencap -p > shots/api${API}_podcast.png
adb shell am start -n $M --es open_tab 4; sleep 3; adb exec-out screencap -p > shots/api${API}_more.png
PID=$(adb shell pidof com.tomstechsolutions.jukebox)
adb logcat -d > shots/api${API}_logcat.txt
grep -A 30 "FATAL EXCEPTION" shots/api${API}_logcat.txt | grep -B2 -A 28 "Process: com.tomstechsolutions.jukebox" > shots/api${API}_crash.txt || true
if [ -z "$PID" ] || [ -s shots/api${API}_crash.txt ]; then echo "APP CRASHED on API $API"; cat shots/api${API}_crash.txt; exit 1; fi
echo "API $API OK (pid $PID)"
