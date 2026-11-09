#!/usr/bin/env python3
import json, time, urllib.parse, urllib.request
qs = [("RFI Tiếng Việt","vn"),("RFA Tiếng Việt","us"),("SBS Vietnamese","au"),("Radio Veritas Asia Vietnamese","vn"),("Lời Chúa Mỗi Ngày","vn"),
("The Bible in a Year Ascension","au"),("Catholic Answers Live","au"),("EWTN","au"),("Word on Fire","au"),("Daily Gospel Reflection","au"),("Vatican News English daily","us"),
("7NEWS","au"),("9News","au"),("10 News First","au"),("SBS News in Depth","au"),("The Age","au"),("Herald Sun","au"),
("triple j","au"),("Double J","au"),("ABC Classic","au"),("Song Exploder","au"),("Wow in the World","au"),("Story Pirates","au"),("bedtime stories for kids","au"),
("truyện cổ tích","vn"),("sách nói","vn"),("đọc truyện đêm khuya","vn"),("kể chuyện","vn"),("SBS Giọng ca Việt Úc","au"),("Tạp chí Âm Nhạc RFI","vn"),("Lời Chúa","vn"),("Tin Mừng","vn"),("Công giáo","vn")]
out=[]
for q,c in qs:
    url=f"https://itunes.apple.com/search?media=podcast&country={c}&limit=6&term={urllib.parse.quote(q)}"
    for attempt in range(3):
        try:
            d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"TomsJukebox-CI"}),timeout=20)); break
        except Exception as e:
            d={"results":[]}; time.sleep(10)
    r=[x for x in d.get("results",[]) if x.get("feedUrl")]
    out.append(f"== {q} [{c}] {len(r)}")
    for x in r: out.append(f"   {x.get('collectionId')} | {x.get('collectionName')} | {x.get('artistName')}")
    time.sleep(4)
open("explore.txt","w").write("\n".join(out))
