#!/bin/bash
# Emulator smoke test: install, start, look around, check that the app is still alive, take screenshots.
set -x
API=$1
APK=$(ls app/build/outputs/apk/release/*.apk | head -1)
mkdir -p shots
adb install -r -g "$APK" || adb install -r "$APK"
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
adb shell settings put system user_rotation 0; sleep 2
PID=$(adb shell pidof com.tomstechsolutions.jukebox)
adb logcat -d > shots/api${API}_logcat.txt
grep -A 30 "FATAL EXCEPTION" shots/api${API}_logcat.txt | grep -B2 -A 28 "Process: com.tomstechsolutions.jukebox" > shots/api${API}_crash.txt || true
if [ -z "$PID" ] || [ -s shots/api${API}_crash.txt ]; then echo "APP CRASHED on API $API"; cat shots/api${API}_crash.txt; exit 1; fi
echo "API $API OK (pid $PID)"
