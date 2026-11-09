#!/usr/bin/env python3
import json, urllib.parse, urllib.request
qs = [("BBC Tiếng Việt","vn"),("BBC Vietnamese","us"),("Chân Trời Mới","us"),("Radio Chan Troi Moi","us"),("SBTN","us"),("SBTN Saigon Broadcasting","us"),("Saigon Broadcasting Television","us"),
("Chân Lý Á Châu","us"),("Radio Veritas Asia Tiếng Việt","vn"),("VietCatholic","vn"),("Viet Catholic","us"),("VietVatican","vn"),("Vatican Tiếng Việt","vn"),
("ABC Melbourne","au"),("ABC Radio Melbourne","au"),("ABC Kids","au"),("ABC Kids Listen","au"),("truyện ngắn","vn"),("truyện ngắn audio","vn"),
("nhạc vàng","vn"),("nhạc bolero","vn"),("bolero Việt","vn"),("nhạc xưa Sài Gòn","vn"),("Trịnh Công Sơn","vn"),("nhạc Trịnh Công Sơn","vn"),("Thánh ca Công giáo","vn"),("thánh ca","vn"),
("Vatican News English","us"),("Vatican News","us"),("SBS News","au"),("Catholic Melbourne","au"),("Melbourne Catholic","au"),("7NEWS","au"),("9News","au"),("10 News","au"),("Herald Sun","au"),("The Age","au"),("nhạc việt","vn"),("truyện cổ tích","vn")]
out=[]
for q,c in qs:
    for cc in dict.fromkeys([c,"us","au"]):
        url=f"https://itunes.apple.com/search?media=podcast&country={cc}&limit=8&term={urllib.parse.quote(q)}"
        try: d=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"TomsJukebox-CI"}),timeout=20))
        except Exception as e: d={"results":[]}
        r=[x for x in d.get("results",[]) if x.get("feedUrl")]
        out.append(f"== {q} [{cc}] {len(r)}")
        for x in r: out.append(f"   {x.get('collectionName')} | {x.get('artistName')} | {x.get('collectionId')}")
open("explore.txt","w").write("\n".join(out))
