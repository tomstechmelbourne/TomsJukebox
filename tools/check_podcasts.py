#!/usr/bin/env python3
"""Checks every suggested podcast channel name on Apple Podcasts (run on GitHub Actions at build time).
Reads app/src/main/java/.../data/PodcastGroups.kt and writes podcasts_report.txt."""
import json, re, unicodedata, urllib.parse, urllib.request

SRC = "app/src/main/java/com/tomstechsolutions/jukebox/data/PodcastGroups.kt"
src = open(SRC, encoding="utf-8").read()

def norm(s):
    s = s.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

groups = re.findall(r'PodGroup\("(\w+)", "([^"]+)", "([^"]+)", listOf\((.*?)\)\),', src, re.S)
out = []
for key, en, vi, body in groups:
    out.append(f"== {vi} ({en})")
    for m in re.finditer(r'PodPick\("([^"]+)", "(\w+)"(?:, (\d+))?(?:, must = "([^"]*)")?\)', body):
        q, country, take, must = m.group(1), m.group(2), int(m.group(3) or 1), m.group(4) or ""
        found = []
        for c in dict.fromkeys([country, "us"]):
            url = f"https://itunes.apple.com/search?media=podcast&country={c}&limit=10&term={urllib.parse.quote(q)}"
            try:
                data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "TomsJukebox-CI"}), timeout=20))
            except Exception as e:
                data = {"results": []}
            res = [r for r in data.get("results", []) if r.get("feedUrl")]
            ok = [r for r in res if not must or norm(must) in norm(r.get("collectionName", "") + " " + r.get("artistName", ""))][:take]
            if ok:
                found = ok; break
        if found:
            out.append(f"  OK   {q}: " + " | ".join(r["collectionName"] for r in found))
        else:
            out.append(f"  MISS {q}: không tìm thấy trên Apple Podcasts")
open("podcasts_report.txt", "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
