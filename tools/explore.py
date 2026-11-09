#!/usr/bin/env python3
import json, re, time, urllib.request, email.utils
ids = ["1303342739","1576144144","1896828280","1514580175","1349523628","73329715","1616444281","1536559302","92455788","1571503601","1574624782","1731182745","1571745841","161320292"]
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent":"TomsJukebox/0.9.3 (Android)"}), timeout=30).read()
d = json.loads(get("https://itunes.apple.com/lookup?id=" + ",".join(ids)))
out = []
for r in d["results"]:
    f = r.get("feedUrl"); name = r.get("collectionName")
    try:
        x = get(f).decode("utf-8", "ignore")
        items = re.findall(r"<item[\s>].*?</item>", x, re.S)
        dates = []
        for it in items:
            m = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
            if m:
                try: dates.append(email.utils.parsedate_to_datetime(m.group(1).strip()))
                except Exception: pass
        first = re.search(r"<pubDate>(.*?)</pubDate>", items[0], re.S).group(1) if items else "-"
        out.append(f"{r.get('collectionId')} | {name} | items={len(items)} | first={first.strip()} | newest={max(dates) if dates else '-'} | releaseDate={r.get('releaseDate')} | {f}")
    except Exception as e:
        out.append(f"{r.get('collectionId')} | {name} | ERROR {e} | {f}")
    time.sleep(1)
open("explore.txt","w").write("\n".join(out))
