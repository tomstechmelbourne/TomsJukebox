#!/usr/bin/env python3
"""Checks the suggested podcast channels (Apple Podcasts ids in PodcastGroups.kt) and writes podcasts_report.txt."""
import json, re, time, urllib.request
SRC = "app/src/main/java/com/tomstechsolutions/jukebox/data/PodcastGroups.kt"
src = open(SRC, encoding="utf-8").read()
out = []
for key, en, vi, body in re.findall(r'PodGroup\("(\w+)", "([^"]+)", "([^"]+)", listOf\((.*?)\)(?:, news = true)?\)', src, re.S):
    ids = re.findall(r'"(\d+)"', body)
    got = {}
    for country in ["", "&country=vn", "&country=au"]:
        need = [i for i in ids if i not in got]
        if not need: break
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://itunes.apple.com/lookup?id=" + ",".join(need) + country, headers={"User-Agent": "TomsJukebox-CI"}), timeout=25))
            for r in d.get("results", []):
                if r.get("feedUrl"): got[str(r.get("collectionId"))] = f'{r.get("collectionName")}  (tập mới nhất {r.get("releaseDate","")[:10]})'
        except Exception as e:
            pass
        time.sleep(3)
    out.append(f"== {vi} ({en}): {len(got)}/{len(ids)}")
    for i in ids: out.append(f"  {'OK  ' if i in got else 'MISS'} {i} {got.get(i, '')}")
open("podcasts_report.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
