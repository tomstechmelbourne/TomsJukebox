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
        print(f"{s.get('name','')[:60]!s:60} | {s.get('countrycode','')} | {s.get('state','')[:18]:18} | {s.get('bitrate',0):>3} {s.get('codec','')[:5]:5} | ok={s.get('lastcheckok')} | clicks={s.get('clickcount')} | lang={s.get('language','')[:20]}")
AU = ["SBS", "smooth", "Magic", "1278", "SEN", "RSN", "Racing", "ABC Central", "Bendigo", "2000", "Newcastle", "Gold Coast", "B105", "B 105",
      "RTR", "Northern Tas", "Launceston", "Hobart", "Hit 100", "Hit100", "ABC Radio", "Triple M", "Nova", "KIIS", "Gold 10", "Mix 1", "Hit 10"]
for term in AU:
    show("AU " + term, q(f"/json/stations/search?name={urllib.parse.quote(term)}&countrycode=AU&hidebroken=true&order=clickcount&reverse=true&limit=40"))
show("ALL VN", q("/json/stations/bycountrycodeexact/VN?hidebroken=true&order=clickcount&reverse=true&limit=400"))
show("VIETNAMESE LANGUAGE", q("/json/stations/search?language=vietnamese&hidebroken=true&order=clickcount&reverse=true&limit=300"))
for term in ["SBS Viet", "Vietnam", "Saigon", "Sai Gon", "Little Saigon", "Bolsa", "RFA", "Nhac", "VOV", "VOH", "Ha Noi", "Hanoi"]:
    show("ANY " + term, q(f"/json/stations/search?name={urllib.parse.quote(term)}&hidebroken=true&order=clickcount&reverse=true&limit=40"))
