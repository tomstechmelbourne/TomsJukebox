#!/usr/bin/env python3
import json, time, urllib.parse, urllib.request
qs=["7NEWS","7 News","Seven News","Sunrise 7","10 News","Network 10","The Project 10","10 News First","Herald Sun","The Morning Edition","The Age","news.com.au","The Australian","Sky News Australia","ABC AM","ABC PM","Nine News","A Current Affair","Today Show Australia","3AW","Neil Mitchell","Melbourne news"]
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
open("explore.txt","w").write("\n".join(out))
