import json, urllib.parse, urllib.request
H = ["de1.api.radio-browser.info", "nl1.api.radio-browser.info", "at1.api.radio-browser.info"]
def q(path):
    for h in H:
        try:
            r = urllib.request.Request(f"https://{h}{path}", headers={"User-Agent": "TomsJukebox-build-check/0.9.1"})
            return json.loads(urllib.request.urlopen(r, timeout=20).read().decode())
        except Exception: pass
    return []
def show(title, rows):
    print(f"\n=== {title} ({len(rows)})")
    for s in rows:
        print(f"{s.get('name','')[:50]:50} | {s.get('countrycode','')} | {s.get('bitrate',0):>3} {s.get('codec','')[:5]:5} | ok={s.get('lastcheckok')} | {s.get('url_resolved','')[:110]} | tags={s.get('tags','')[:40]}")
for term in ["SBS", "SBS 1", "SBS Radio", "SBS Vietnamese", "SBS Viet"]:
    show("ANY " + term, q(f"/json/stations/search?name={urllib.parse.quote(term)}&hidebroken=false&order=bitrate&reverse=true&limit=60"))
show("TAG sbs", q("/json/stations/search?tag=sbs&hidebroken=false&limit=60"))
