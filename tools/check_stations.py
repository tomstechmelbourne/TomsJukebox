"""Checks every built-in station on Radio Browser (run by GitHub Actions at build time) and writes a report."""
import json, re, sys, urllib.parse, urllib.request
src = open('app/src/main/java/com/tomstechsolutions/jukebox/data/Stations.kt', encoding='utf-8').read()
rows = re.findall(r'Station\("((?:[^"\\]|\\.)*)", "((?:[^"\\]|\\.)*)", "(\w+)", "(\w+)", "(\w+)"\)', src)
hosts = ["de1.api.radio-browser.info", "nl1.api.radio-browser.info", "at1.api.radio-browser.info"]
def q(path):
    for h in hosts:
        try:
            req = urllib.request.Request(f"https://{h}{path}", headers={"User-Agent": "TomsJukebox-build-check/0.9.1"})
            return json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
        except Exception:
            continue
    return None
ok = bad = 0
out = []
for name, search, country, group, genre in rows:
    cc = {"AU": "&countrycode=AU", "VN": "&countrycode=VN"}.get(country, "")
    r = q(f"/json/stations/search?name={urllib.parse.quote(search)}{cc}&hidebroken=true&order=clickcount&reverse=true&limit=5")
    if r is None:
        out.append(f"?  {name}  (server not reachable)"); continue
    if not r and cc and country == 'OS':
        r = q(f"/json/stations/search?name={urllib.parse.quote(search)}&hidebroken=true&order=clickcount&reverse=true&limit=5") or []
    if r:
        ok += 1; top = r[0]
        out.append(f"OK {name:34s} -> {top.get('name','')[:40]:40s} {top.get('bitrate',0)} kbps {top.get('codec','')}")
    else:
        bad += 1; out.append(f"-- {name:34s} -> NOT FOUND (shows as Tạm Ngưng)")
report = f"Stations: {len(rows)}  found: {ok}  not found: {bad}\n" + "\n".join(out)
open('stations_report.txt', 'w', encoding='utf-8').write(report)
print(report)
