"""Internet radio: Australian and Vietnamese stations, location-aware local stations, ICY stream reader.

Station stream addresses change often, so each built-in station is looked up by name on the free
Radio Browser directory (radio-browser.info) the first time it is played, then remembered."""
import json
import random
import re
import threading
import time
import urllib.parse
import urllib.request

from .app_info import log
from .online import UA

STATES = ["VIC", "NSW", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
STATE_NAMES = {"VIC": "Victoria", "NSW": "New South Wales", "QLD": "Queensland", "SA": "South Australia",
               "WA": "Western Australia", "TAS": "Tasmania", "NT": "Northern Territory",
               "ACT": "Australian Capital Territory"}
STATE_CITY = {"VIC": "Melbourne", "NSW": "Sydney", "QLD": "Brisbane", "SA": "Adelaide", "WA": "Perth",
              "TAS": "Hobart", "NT": "Darwin", "ACT": "Canberra"}

# key, name, group, state, query (Radio Browser name search), country code
BUILTIN = [   # the same stations as the Android app (looked up on Radio Browser by name when played)
    ('a_sbs_ti_ng_vi_t_sbs_radio_1', 'SBS Tiếng Việt (SBS Radio 1)', 'au', '', 'SBS Radio 1', 'AU', 'https://sbs-ice.streamguys1.com/sbs1-sbs-web'),
    ('a_abc_newsradio', 'ABC NewsRadio', 'au', '', 'ABC NewsRadio', 'AU', ''),
    ('a_abc_radio_national', 'ABC Radio National', 'au', '', 'ABC Radio National', 'AU', ''),
    ('a_triple_j', 'triple j', 'au', '', 'triple j', 'AU', ''),
    ('a_double_j', 'Double J', 'au', '', 'Double J', 'AU', ''),
    ('a_triple_j_unearthed', 'triple j Unearthed', 'au', '', 'triple j Unearthed', 'AU', ''),
    ('a_abc_classic', 'ABC Classic', 'au', '', 'ABC Classic', 'AU', ''),
    ('a_abc_classic_2', 'ABC Classic 2', 'au', '', 'ABC Classic 2', 'AU', ''),
    ('a_abc_jazz', 'ABC Jazz', 'au', '', 'ABC Jazz', 'AU', ''),
    ('a_abc_country', 'ABC Country', 'au', '', 'ABC Country', 'AU', ''),
    ('a_abc_kids_listen', 'ABC Kids Listen', 'au', '', 'ABC Kids listen', 'AU', ''),
    ('a_sbs_radio_1', 'SBS Radio 1', 'au', '', 'SBS Radio 1', 'AU', ''),
    ('a_sbs_popasia', 'SBS PopAsia', 'au', '', 'SBS PopAsia', 'AU', ''),
    ('a_sbs_chill', 'SBS Chill', 'au', '', 'SBS Chill', 'AU', ''),
    ('a_abc_sport', 'ABC Sport', 'au', '', 'ABC Sport', 'AU', ''),
    ('a_abc_melbourne_774', 'ABC Melbourne 774', 'au_local', 'VIC', 'ABC Radio Melbourne', 'AU', ''),
    ('a_3aw_693', '3AW 693', 'au_local', 'VIC', '3AW', 'AU', ''),
    ('a_gold_104_3', 'Gold 104.3', 'au_local', 'VIC', 'Gold 104.3', 'AU', ''),
    ('a_smoothfm_91_5', 'smoothfm 91.5', 'au_local', 'VIC', 'Smooth FM 91.5', 'AU', ''),
    ('a_3mbs_103_5', '3MBS 103.5', 'au_local', 'VIC', '3MBS', 'AU', ''),
    ('a_nova_100', 'Nova 100', 'au_local', 'VIC', 'Nova 100', 'AU', ''),
    ('a_kiis_101_1', 'KIIS 101.1', 'au_local', 'VIC', 'KIIS 101.1', 'AU', ''),
    ('a_triple_m_melbourne', 'Triple M Melbourne', 'au_local', 'VIC', 'Triple M Melbourne', 'AU', ''),
    ('a_rsn_927', 'RSN 927', 'au_local', 'VIC', 'RSN 927', 'AU', ''),
    ('a_pbs_106_7', 'PBS 106.7', 'au_local', 'VIC', 'PBS 106.7', 'AU', ''),
    ('a_triple_r_102_7', 'Triple R 102.7', 'au_local', 'VIC', '3RRR', 'AU', ''),
    ('a_3cr_855', '3CR 855', 'au_local', 'VIC', '3CR', 'AU', ''),
    ('a_3zzz_92_3', '3ZZZ 92.3', 'au_local', 'VIC', '3ZZZ', 'AU', ''),
    ('a_joy_94_9', 'JOY 94.9', 'au_local', 'VIC', 'JOY 94.9', 'AU', ''),
    ('a_abc_ballarat', 'ABC Ballarat', 'au_local', 'VIC', 'ABC Ballarat', 'AU', ''),
    ('a_abc_sydney_702', 'ABC Sydney 702', 'au_local', 'NSW', 'ABC Radio Sydney', 'AU', ''),
    ('a_2gb_873', '2GB 873', 'au_local', 'NSW', '2GB', 'AU', ''),
    ('a_kiis_1065', 'KIIS 1065', 'au_local', 'NSW', 'KIIS 1065', 'AU', ''),
    ('a_nova_96_9', 'Nova 96.9', 'au_local', 'NSW', 'Nova 96.9', 'AU', ''),
    ('a_triple_m_sydney', 'Triple M Sydney', 'au_local', 'NSW', 'Triple M Sydney', 'AU', ''),
    ('a_2day_fm_104_1', '2Day FM 104.1', 'au_local', 'NSW', '2Day FM', 'AU', ''),
    ('a_smoothfm_95_3', 'smoothfm 95.3', 'au_local', 'NSW', 'Smooth FM 95.3', 'AU', ''),
    ('a_wsfm_101_7', 'WSFM 101.7', 'au_local', 'NSW', 'WSFM', 'AU', ''),
    ('a_2ser_107_3', '2SER 107.3', 'au_local', 'NSW', '2SER', 'AU', ''),
    ('a_hope_103_2', 'Hope 103.2', 'au_local', 'NSW', 'Hope 103.2', 'AU', ''),
    ('a_abc_newcastle', 'ABC Newcastle', 'au_local', 'NSW', 'ABC Radio Newcastle', 'AU', ''),
    ('a_abc_brisbane_612', 'ABC Brisbane 612', 'au_local', 'QLD', 'ABC Radio Brisbane', 'AU', ''),
    ('a_4bc_882', '4BC 882', 'au_local', 'QLD', '4BC', 'AU', ''),
    ('a_abc_gold_coast', 'ABC Gold Coast', 'au_local', 'QLD', 'ABC Radio Gold Coast', 'AU', ''),
    ('a_nova_106_9', 'Nova 106.9', 'au_local', 'QLD', 'Nova 106.9', 'AU', ''),
    ('a_kiis_97_3', 'KIIS 97.3', 'au_local', 'QLD', 'KIIS 97.3', 'AU', ''),
    ('a_triple_m_brisbane', 'Triple M Brisbane', 'au_local', 'QLD', 'Triple M Brisbane', 'AU', ''),
    ('a_hot_tomato', 'Hot Tomato', 'au_local', 'QLD', 'Hot Tomato', 'AU', ''),
    ('a_4zzz_102_1', '4ZZZ 102.1', 'au_local', 'QLD', '4ZZZ', 'AU', ''),
    ('a_4mbs_classic_fm', '4MBS Classic FM', 'au_local', 'QLD', '4MBS', 'AU', ''),
    ('a_abc_adelaide_891', 'ABC Adelaide 891', 'au_local', 'SA', 'ABC Radio Adelaide', 'AU', ''),
    ('a_fiveaa', 'FIVEaa', 'au_local', 'SA', 'FIVEaa', 'AU', ''),
    ('a_mix_102_3', 'Mix 102.3', 'au_local', 'SA', 'Mix 102.3', 'AU', ''),
    ('a_nova_91_9', 'Nova 91.9', 'au_local', 'SA', 'Nova 91.9', 'AU', ''),
    ('a_triple_m_adelaide', 'Triple M Adelaide', 'au_local', 'SA', 'Triple M Adelaide', 'AU', ''),
    ('a_cruise_1323', 'Cruise 1323', 'au_local', 'SA', 'Cruise 1323', 'AU', ''),
    ('a_three_d_radio', 'Three D Radio', 'au_local', 'SA', 'Three D Radio', 'AU', ''),
    ('a_abc_perth_720', 'ABC Perth 720', 'au_local', 'WA', 'ABC Radio Perth', 'AU', ''),
    ('a_6pr_882', '6PR 882', 'au_local', 'WA', '6PR', 'AU', ''),
    ('a_mix_94_5', 'Mix 94.5', 'au_local', 'WA', 'Mix 94.5', 'AU', ''),
    ('a_nova_93_7', 'Nova 93.7', 'au_local', 'WA', 'Nova 93.7', 'AU', ''),
    ('a_rtrfm_92_1', 'RTRFM 92.1', 'au_local', 'WA', 'RTR FM', 'AU', ''),
    ('a_6ix', '6iX', 'au_local', 'WA', '6iX', 'AU', ''),
    ('a_abc_hobart_936', 'ABC Hobart 936', 'au_local', 'TAS', 'ABC Radio Hobart', 'AU', ''),
    ('a_abc_northern_tasmania', 'ABC Northern Tasmania', 'au_local', 'TAS', 'ABC Radio Northern Tasmania', 'AU', ''),
    ('a_edge_radio_99_3', 'Edge Radio 99.3', 'au_local', 'TAS', 'Edge Radio', 'AU', ''),
    ('a_abc_darwin_105_7', 'ABC Darwin 105.7', 'au_local', 'NT', 'ABC Radio Darwin', 'AU', ''),
    ('a_hot_100_darwin', 'Hot 100 Darwin', 'au_local', 'NT', 'Hot 100', 'AU', ''),
    ('a_mix_104_9_darwin', 'Mix 104.9 Darwin', 'au_local', 'NT', 'Mix 104.9', 'AU', ''),
    ('a_territory_fm', 'Territory FM', 'au_local', 'NT', 'Territory FM', 'AU', ''),
    ('a_abc_canberra_666', 'ABC Canberra 666', 'au_local', 'ACT', 'ABC Radio Canberra', 'AU', ''),
    ('a_2cc_1206', '2CC 1206', 'au_local', 'ACT', '2CC', 'AU', ''),
    ('a_mix_106_3', 'Mix 106.3', 'au_local', 'ACT', 'Mix 106.3', 'AU', ''),
    ('a_artsound_fm_92_7', 'ArtSound FM 92.7', 'au_local', 'ACT', 'ArtSound', 'AU', ''),
    ('a_2xx_98_3', '2XX 98.3', 'au_local', 'ACT', '2XX', 'AU', ''),
    ('a_vov1_th_i_s', 'VOV1 – Thời Sự', 'vn', '', 'VOV1', 'VN', ''),
    ('a_vov2_v_n_ho_x_h_i', 'VOV2 – Văn Hoá Xã Hội', 'vn', '', 'VOV2', 'VN', ''),
    ('a_vov3_m_nh_c', 'VOV3 – Âm Nhạc', 'vn', '', 'VOV3', 'VN', ''),
    ('a_vov_giao_th_ng_h_n_i', 'VOV Giao Thông Hà Nội', 'vn', '', 'VOV Giao Thong Ha Noi', 'VN', ''),
    ('a_vov_giao_th_ng_tp_hcm', 'VOV Giao Thông TP.HCM', 'vn', '', 'VOV GT HCM', 'VN', ''),
    ('a_h_n_i_fm_90', 'Hà Nội FM 90', 'vn', '', 'FM HANOI 90', 'VN', ''),
    ('a_h_n_i_fm_96', 'Hà Nội FM 96', 'vn', '', 'FM HANOI 96', 'VN', ''),
    ('a_h_i_ph_ng_fm_102_2', 'Hải Phòng FM 102.2', 'vn', '', 'Hai Phong FM', 'VN', ''),
    ('a_3zzz_c_gi_ti_ng_vi_t', '3ZZZ (Có Giờ Tiếng Việt)', 'vn', '', '3ZZZ', '', ''),
    ('a_little_saigon_radio', 'Little Saigon Radio', 'vn', '', 'Little Saigon Radio', '', ''),
    ('a_sen_track', 'SEN Track', 'au_local', 'VIC', 'SEN Track', 'AU', ''),
    ('a_abc_gippsland', 'ABC Gippsland', 'au_local', 'VIC', 'ABC Radio Gippsland', 'AU', ''),
    ('a_1170_sen_sydney', '1170 SEN Sydney', 'au_local', 'NSW', '1170 SEN', 'AU', ''),
    ('a_abc_illawarra', 'ABC Illawarra', 'au_local', 'NSW', 'ABC Radio Illawarra', 'AU', ''),
    ('a_senq', 'SENQ', 'au_local', 'QLD', 'SENQ', 'AU', ''),
    ('a_smooth_fm_brisbane', 'Smooth FM Brisbane', 'au_local', 'QLD', 'Smooth FM Brisbane', 'AU', ''),
    ('a_abc_sunshine_coast', 'ABC Sunshine Coast', 'au_local', 'QLD', 'ABC Radio Sunshine Coast', 'AU', ''),
    ('a_smooth_fm_adelaide', 'Smooth FM Adelaide', 'au_local', 'SA', 'Smooth FM Adelaide', 'AU', ''),
    ('a_smooth_fm_perth', 'Smooth FM Perth', 'au_local', 'WA', 'Smooth FM Perth', 'AU', ''),
    ('a_7ho_fm_hobart', '7HO FM Hobart', 'au_local', 'TAS', '7HOFM', 'AU', ''),
    ('a_ultra_106_5_hobart', 'Ultra 106.5 Hobart', 'au_local', 'TAS', 'Ultra 106.5', 'AU', ''),
    ('a_abc_alice_springs', 'ABC Alice Springs', 'au_local', 'NT', 'ABC Radio Alice Springs', 'AU', ''),
    ('a_sbs_popdesi', 'SBS PopDesi', 'au', '', 'SBS PopDesi', 'AU', ''),
    ('a_h_n_i_community_radio', 'Hà Nội Community Radio', 'vn', '', 'Hà Nội Community', 'VN', ''),
    ('a_rfi_ti_ng_vi_t', 'RFI Tiếng Việt', 'vn', '', 'RFI Tiếng Việt', '', ''),
    ('a_rva_ti_ng_vi_t_vatican', 'RVA Tiếng Việt (Vatican)', 'vn', '', 'RVA Vietnamese', '', ''),
    ('a_bolsa_radio', 'Bolsa Radio', 'vn', '', 'Bolsa Radio VN', '', ''),
    ('a_saigon_houston_am900', 'Saigon Houston AM900', 'vn', '', 'Saigon Houston AM900', '', ''),
    ('a_saigon_radio_106_3_fm', 'Saigon Radio 106.3 FM', 'vn', '', 'Saigon Radio 106.3', '', ''),
    ('a_viet_washington_dc', 'Viet Washington DC', 'vn', '', 'VIET WASHINGTON DC', '', ''),
    ('a_viet_radio_1560', 'Viet Radio 1560', 'vn', '', 'VIET RADIO 1560', '', ''),
    ('a_tnt_atlanta_radio', 'TNT Atlanta Radio', 'vn', '', 'TNT Atlanta Radio', '', ''),
    ('a_kali_saigon', 'Kali Saigon', 'vn', '', 'KALI SAIGON', '', ''),
    ('a_zing_bolero', 'Zing Bolero', 'vn', '', 'ZING BOLERO', '', ''),
    ('a_m_radio_vietnam', 'M Radio Vietnam', 'vn', '', 'M Radio Vietnam', '', ''),
]

API_HOSTS = ["de1.api.radio-browser.info", "nl1.api.radio-browser.info", "at1.api.radio-browser.info",
             "de2.api.radio-browser.info", "fi1.api.radio-browser.info"]


def seed(db):
    """Insert built-in stations once (keeps Tom's favourites and edits)."""
    keys = set()
    for i, (key, name, grp, state, query, cc, url) in enumerate(BUILTIN):
        keys.add(key)
        if not db.one("SELECT id FROM stations WHERE builtin_key=?", (key,)):
            db.x("INSERT INTO stations(name,grp,state,city,query,builtin_key,sort,homepage,url) VALUES(?,?,?,?,?,?,?,?,?)",
                 (name, grp, state, STATE_CITY.get(state, ""), json.dumps([query, cc]), key, i, "", url or None), commit=False)
        else:
            db.x("UPDATE stations SET sort=? WHERE builtin_key=?", (i, key), commit=False)
    # older built-in stations that could not be found any more are dropped (unless Tom made them a favourite)
    for r in db.q("SELECT id, builtin_key FROM stations WHERE builtin_key IS NOT NULL AND custom=0 AND fav=0"):
        if r["builtin_key"] not in keys:
            db.x("DELETE FROM stations WHERE id=?", (r["id"],), commit=False)
    db.commit()


# ------------------------------------------------------------------ Radio Browser
def _api(path, params):
    hosts = API_HOSTS[:]
    random.shuffle(hosts)
    last = None
    for h in hosts[:3]:
        try:
            url = f"https://{h}/json/{path}?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except Exception as e:
            last = e
    raise OSError(f"radio directory not reachable: {last}")


def search(name=None, countrycode=None, state=None, language=None, limit=40):
    p = {"hidebroken": "true", "order": "votes", "reverse": "true", "limit": limit}
    if name:
        p["name"] = name
    if countrycode:
        p["countrycode"] = countrycode
    if state:
        p["state"] = state
    if language:
        p["language"] = language
    rows = _api("stations/search", p)
    out = []
    for r in rows:
        url = r.get("url_resolved") or r.get("url")
        if not url:
            continue
        out.append({"name": (r.get("name") or "").strip(), "url": url, "homepage": r.get("homepage") or "",
                    "codec": (r.get("codec") or "").upper(), "bitrate": int(r.get("bitrate") or 0),
                    "state": r.get("state") or "", "uuid": r.get("stationuuid"), "votes": r.get("votes", 0)})
    return out


def resolve_station(db, row):
    """Find a stream URL for a built-in station that has none yet (or whose URL failed)."""
    try:
        query, cc = json.loads(row["query"] or "[]") or (row["name"], "")
    except ValueError:
        query, cc = row["name"], ""
    res = search(name=query, countrycode=cc or None, limit=10)
    if not res:
        res = search(name=query, limit=10)
    if not res:
        return None
    best = max(res, key=lambda r: (r["votes"], r["bitrate"]))
    db.x("UPDATE stations SET url=?, codec=?, bitrate=?, homepage=? WHERE id=?",
         (best["url"], best["codec"], best["bitrate"], best["homepage"], row["id"]))
    return best["url"]


def nearby(state):
    """Local stations of a state (Radio Browser), plus Vietnamese-language stations in Australia."""
    out = []
    try:
        out = search(countrycode="AU", state=STATE_NAMES.get(state, state), limit=40)
    except OSError as e:
        log.info("nearby failed: %s", e)
    return out


def vietnamese_in_australia():
    try:
        return search(countrycode="AU", language="vietnamese", limit=30)
    except OSError:
        return []


# ------------------------------------------------------------------ where am I?
_VIC_NSW = [(140.97, -34.0), (142.15, -34.15), (142.77, -34.6), (143.55, -35.30), (144.75, -36.10),
            (145.5, -35.85), (146.38, -35.97), (146.9, -36.10), (147.4, -36.02), (148.2, -36.8), (149.98, -37.5)]


def _interp(pts, x):
    if x <= pts[0][0]:
        return pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return pts[-1][1]


def state_from_latlon(lat, lon):
    """Approximate Australian state from coordinates (offline, borders simplified)."""
    if not (-44.5 < lat < -9 and 112 < lon < 154.5):
        return None
    if 148.76 <= lon <= 149.4 and -35.92 <= lat <= -35.12:
        return "ACT"
    if lat < -39.4 and lon > 143.5:
        return "TAS"
    if lon < 129:
        return "WA"
    if lon < 138:
        return "NT" if lat > -26 else "SA"
    if lon < 141:
        return "QLD" if lat > -26 else "SA"
    border = -29.0 if lon <= 150 else -29.0 + (lon - 150) * (0.84 / 3.6)
    if lat > border:
        return "QLD"
    if lat < _interp(_VIC_NSW, lon):
        return "VIC"
    return "NSW"


def windows_location():
    """(lat, lon) from Windows Location (Wi-Fi based on laptops). None if off / not allowed."""
    try:
        import asyncio
        from winrt.windows.devices.geolocation import Geolocator  # pywinrt package

        async def _get():
            loc = Geolocator()
            pos = await loc.get_geoposition_async()
            p = pos.coordinate.point.position
            return p.latitude, p.longitude
        return asyncio.run(asyncio.wait_for(_get(), 20))
    except Exception as e:
        log.info("windows location not available: %s", e)
        return None


def ip_state():
    """Guess the state from the internet connection (less accurate on 4G / VPN)."""
    for url, key in (("https://ipapi.co/json/", "region_code"), ("https://ipwho.is/", "region_code")):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=8) as r:
                d = json.loads(r.read().decode("utf-8"))
            if (d.get("country_code") or d.get("country")) not in ("AU", "Australia"):
                return None
            code = (d.get(key) or "").upper()
            if code in STATES:
                return code
        except Exception:
            continue
    return None


def detect_state(use_windows=True, use_ip=True):
    """Returns (state or None, method)."""
    if use_windows:
        ll = windows_location()
        if ll:
            s = state_from_latlon(*ll)
            if s:
                return s, "windows"
    if use_ip:
        s = ip_state()
        if s:
            return s, "ip"
    return None, ""


# ------------------------------------------------------------------ stream reading
def resolve_playlist(url):
    """.pls / .m3u playlists -> first stream URL. .m3u8 (HLS) is left for FFmpeg."""
    low = url.lower().split("?")[0]
    if not (low.endswith(".pls") or (low.endswith(".m3u") and not low.endswith(".m3u8"))):
        return url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            text = r.read(65536).decode("utf-8", "replace")
        for line in text.splitlines():
            line = line.strip()
            m = re.match(r"(?:File\d+=)?(https?://\S+)", line)
            if m:
                return m.group(1)
    except Exception as e:
        log.info("playlist resolve failed: %s", e)
    return url


class IcyStream:
    """File-like reader for Shoutcast/Icecast streams: strips the in-band song titles and keeps them."""

    def __init__(self, url, want_meta=True):
        self.url = resolve_playlist(url)
        req = urllib.request.Request(self.url, headers={"User-Agent": UA, "Icy-MetaData": "1" if want_meta else "0"})
        self.resp = urllib.request.urlopen(req, timeout=15)
        h = self.resp.headers
        self.content_type = (h.get("Content-Type") or "").lower()
        self.metaint = int(h.get("icy-metaint") or 0) if want_meta else 0
        self.station_name = h.get("icy-name") or ""
        self.bitrate = int(re.sub(r"\D", "", h.get("icy-br") or "0") or 0)
        self.left = self.metaint
        self.title = ""
        self.title_changed = threading.Event()
        self.closed = False
        self.bytes_read = 0

    @property
    def fmt(self):
        ct = self.content_type
        if "mpeg" in ct or "mp3" in ct:
            return "mp3"
        if "aac" in ct or "aacp" in ct:
            return "aac"
        if "ogg" in ct or "opus" in ct:
            return "ogg"
        if "flac" in ct:
            return "flac"
        return None

    @property
    def ext(self):
        return {"mp3": ".mp3", "aac": ".aac", "ogg": ".ogg", "flac": ".flac"}.get(self.fmt, ".mp3")

    def _raw(self, n):
        out = b""
        while len(out) < n and not self.closed:
            chunk = self.resp.read(n - len(out))
            if not chunk:
                break
            out += chunk
        return out

    def read(self, n=-1):
        if self.closed:
            return b""
        if n is None or n < 0:
            n = 16384
        if not self.metaint:
            d = self._raw(n)
            self.bytes_read += len(d)
            return d
        out = b""
        while len(out) < n and not self.closed:
            take = min(n - len(out), self.left)
            if take > 0:
                d = self._raw(take)
                if not d:
                    break
                out += d
                self.left -= len(d)
            if self.left == 0:
                ln = self._raw(1)
                if not ln:
                    break
                size = ln[0] * 16
                if size:
                    meta = self._raw(size).rstrip(b"\0").decode("utf-8", "replace")
                    m = re.search(r"StreamTitle='(.*?)';", meta)
                    if m and m.group(1) != self.title:
                        self.title = m.group(1).strip()
                        self.title_changed.set()
                self.left = self.metaint
        self.bytes_read += len(out)
        return out

    def close(self):
        self.closed = True
        try:
            self.resp.close()
        except Exception:
            pass


def open_radio_source(url):
    """Returns an engine Source for a station URL (Shoutcast/Icecast or HLS)."""
    from .engine import AVSource
    low = url.lower().split("?")[0]
    if low.endswith(".m3u8"):
        src = AVSource(url, live=True, duration=0)
        src.icy = None
        return src
    icy = IcyStream(url)
    src = AVSource(icy, fmt=icy.fmt, live=True, duration=0)
    src.icy = icy
    _orig_close = src.close

    def close():
        icy.close()
        _orig_close()
    src.close = close
    return src


def quality_text(codec, bitrate):
    if not bitrate:
        return codec or ""
    tag = "★★★" if bitrate >= 192 else ("★★" if bitrate >= 128 else "★")
    return f"{codec or ''} {bitrate} kbps {tag}".strip()


def now():
    return time.time()
