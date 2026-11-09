#!/usr/bin/env python3
import json, time, urllib.parse, urllib.request
qs=["SBS One","SBS","SBS Radio 1","SBS Radio","10 Comedy","10 comedy podcast","Network 10 comedy","The Project","Have You Been Paying Attention","Hughesy We Have A Problem","Gogglebox Australia","Taskmaster Australia","Thank God You're Here","SBS Comedy","Comedy Australia"]
out=[]
for q in qs:
    u=f"https://itunes.apple.com/search?media=podcast&country=au&limit=8&term={urllib.parse.quote(q)}"
    for a in range(3):
        try: d=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"TomsJukebox-CI"}),timeout=20)); break
        except Exception: d={"results":[]}; time.sleep(10)
    out.append(f"== {q}")
    for r in d.get("results",[]):
        if r.get("feedUrl"): out.append(f"   {r.get('collectionId')} | {r.get('releaseDate','')[:10]} | {r.get('collectionName')} | {r.get('artistName')}")
    time.sleep(4)
# Radio Browser: SBS / 10 streams
for q in ["SBS","10 Comedy","Network 10"]:
    try:
        d=json.load(urllib.request.urlopen(urllib.request.Request("https://de1.api.radio-browser.info/json/stations/byname/"+urllib.parse.quote(q)+"?hidebroken=true&limit=40",headers={"User-Agent":"TomsJukebox-CI"}),timeout=20))
        out.append(f"== RADIO {q}")
        for s in d: out.append(f"   {s.get('name')} | {s.get('countrycode')} | {s.get('codec')} {s.get('bitrate')} | {s.get('url_resolved')}")
    except Exception as e: out.append(f"== RADIO {q} ERR {e}")
open("explore.txt","w").write("\n".join(out))
