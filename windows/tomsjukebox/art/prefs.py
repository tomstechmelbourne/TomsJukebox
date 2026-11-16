"""Settings shared with the Android app (same names, same defaults), saved in the database as one JSON block.
Code ported from Android reads them the same way: Prefs.viz.value, Prefs.skin.value = "glass" ..."""
import json

DEFAULTS = {
    "lang": ("lang", "vi"),
    "theme": ("theme", "toms"),
    "customAccent": ("custom_accent", 0xFFFBB040),
    "skin": ("skin", "pill"),
    "xpColour": ("xp_colour", "blue"),
    "barColour": ("bar_colour", "#FBB040"),
    "customBar": ("custom_bar", 0xFF48B0C8),
    "textScale": ("text_scale", 1.0),
    "pillAlpha": ("pill_alpha", 1.0),
    "waveStrength": ("wave_strength", 1.0),
    "waveHeight": ("wave_height", 0.6),
    "pillColour": ("pill_colour", 0),
    "dblTapColour": ("dbl_tap_colour", True),
    "woodType": ("wood_type", 0),
    "marbleType": ("marble_type", 0),
    "btnStyle": ("btn_style", 0),
    "btnColour": ("btn_colour", "white"),
    "btnCustom": ("btn_custom", 0xFFFFFFFF),
    "btnScale": ("btn_scale", 1.0),
    "pack": ("pack", -1),
    "favStyles": ("fav_styles", ""),
    "recentStyles": ("recent_styles", ""),
    "miniSize": ("mini_size", "medium"),
    "cardBg": ("card_bg", "cover"),
    "cardViz": ("card_viz", True),
    "playerStyle": ("player_style", "card"),
    "lockStyle": ("lock_style", "card"),
    "navFx": ("nav_fx", "glow"),
    "navHaptic": ("nav_haptic", True),
    "fxSpeed": ("fx_speed", 1.0),
    "splashStyle": ("splash_style", 0),
    "splashOn": ("splash_on", True),
    "splashFast": ("splash_fast", False),
    "splashHaptic": ("splash_haptic", True),
    "chipsAutoHide": ("chips_auto_hide", True),
    "libChip": ("lib_chip", 0),
    "viz": ("viz", 0),
    "vizAuto": ("viz_auto", False),
    "vizOn": ("viz_on", True),
    "vizPill": ("viz_pill", True),
    "vizStrip": ("viz_strip", True),
    "vizNav": ("viz_nav", True),
    "realViz": ("real_viz", False),
    "vizSpeed": ("viz_speed", 1.0),
    "edgeOn": ("edge_on", True),
    "edgeEffect": ("edge_effect", 0),
    "edgeSpeed": ("edge_speed", 2),
    "edgeColour": ("edge_colour", "cover"),
    "edgeCustom": ("edge_custom", 0xFF48B0C8),
    "edgeThick": ("edge_thick", 4),
    "edgeBright": ("edge_bright", 0.9),
    "edgeWhere": ("edge_where", "both"),
    "edgeBeat": ("edge_beat", True),
    "edgeAuto": ("edge_auto", False),
    "edgeScreen": ("edge_screen", True),
    "edgeRandom": ("edge_random", False),
    "edgeCorner": ("edge_corner", -1),
    "eqPreset": ("eq_preset", "flat"),
    "eqCustom": ("eq_custom", ""),
    "eqBands": ("eq_bands", "0,0,0,0,0,0,0,0,0,0"),
    "eqAutoGenre": ("eq_auto_genre", False),
    "eqOn": ("eq_on", True),
    "bass": ("bass", 0),
    "treble": ("treble", 0),
    "sleepMinutes": ("sleep_minutes", 30),
    "sleepFade": ("sleep_fade", 60),
    "sleepBluetooth": ("sleep_bt", False),
    "haptics": ("haptics", True),
    "shakeSkip": ("shake_skip", False),
    "swipePill": ("swipe_pill", True),
    "autoPlayHeadset": ("autoplay_headset", False),
    "customLock": ("custom_lock", False),
    "lockY": ("lock_y", -1),
    "lockX": ("lock_x", 0.5),
    "lockYLand": ("lock_y_land", -1),
    "lockXLand": ("lock_x_land", 0.5),
    "lockLocked": ("lock_locked", False),
    "lockSnap": ("lock_snap", True),
    "lockSize": ("lock_size", "medium"),
    "lockAlpha": ("lock_alpha", 1.0),
    "widgetBg": ("widget_bg", "skin"),
    "widgetAlpha": ("widget_alpha", 0.85),
    "batterySaver": ("battery_saver", True),
    "spinBeat": ("spin_beat", True),
    "blurBg": ("blur_bg", True),
    "headsetTriple": ("headset_triple", True),
    "radioState": ("radio_state", "VIC"),
    "radioAutoState": ("radio_auto_state", True),
    "radioHq": ("radio_hq", False),
    "recFolder": ("rec_folder", ""),
    "folders": ("folders", ""),
    "favourites": ("favourites", ""),
    "hidden": ("hidden", ""),
    "podcasts": ("podcasts", "[]"),
    "podNotify": ("pod_notify", ""),
    "podAutoDl": ("pod_auto_dl", ""),
    "podKeep": ("pod_keep", 5),
    "podSpeed": ("pod_speed", "{}"),
    "podSkip": ("pod_skip", "{}"),
    "podHidden": ("pod_hidden", ""),
    "podPlayed": ("pod_played", ""),
    "podSeen": ("pod_seen", "{}"),
    "podNew": ("pod_new", ""),
    "radioFavs": ("radio_favs", ""),
    "podHQ": ("pod_hq", True),
    "fontTitle": ("font_title", "default"),
    "fontBody": ("font_body", "default"),
    "recStyle": ("rec_style", 1),
    "recColour": ("rec_colour", "red"),
    "recCustom": ("rec_custom", 0xFFFF3B3B),
    "recBlink": ("rec_blink", True),
    "waveCols": ("wave_cols", "vivid"),
    "waveShape": ("wave_shape", 0),
    "podAutoSave": ("pod_auto_save", ""),
    "podSavedUrls": ("pod_saved_urls", ""),
    "playlists": ("playlists", "{}"),
    "lastQueue": ("last_queue", "[]"),
    "lastIndex": ("last_index", 0),
    "lastPos": ("last_pos", 0),
    "shortcuts": ("shortcuts", ""),
    "lastBackup": ("last_backup", 0),}

# Windows-only additions
DEFAULTS.update({
    "winOnTop": ("win_on_top", False),
    "miniOnTop": ("mini_on_top", True),
    "trayIcon": ("tray_icon", True),
    "closeToTray": ("close_to_tray", False),
    "panel": ("panel", "lib"),
    "showEq": ("show_eq", False),
    "showLyrics": ("show_lyrics", False),
    "showList": ("show_list", True),
    "winGeom": ("win_geom", ""),
    "miniGeom": ("mini_geom", ""),
    "edgeWin": ("edge_win", True),
})

_listeners = []


class Pref:
    __slots__ = ("name", "key", "default", "_v")

    def __init__(self, name, key, default):
        self.name, self.key, self.default, self._v = name, key, default, default

    @property
    def value(self):
        return self._v

    @value.setter
    def value(self, v):
        if isinstance(self.default, bool):
            v = bool(v)
        elif isinstance(self.default, float):
            v = float(v)
        elif isinstance(self.default, int) and not isinstance(v, bool):
            try:
                v = int(v)
            except (TypeError, ValueError):
                v = self.default
        changed = v != self._v
        self._v = v
        Prefs._save()
        if changed:
            for f in list(_listeners):
                try:
                    f(self.name)
                except Exception:
                    pass


class _Prefs:
    def __init__(self):
        self._db = None
        self._loading = False
        for name, (key, d) in DEFAULTS.items():
            object.__setattr__(self, name, Pref(name, key, d))

    def bind(self, db):
        """Load from the database (key 'android_prefs')."""
        self._db = db
        self._loading = True
        try:
            raw = db.get("android_prefs") if db else None
            data = json.loads(raw) if raw else {}
        except Exception:
            data = {}
        for name, (key, d) in DEFAULTS.items():
            if key in data:
                getattr(self, name)._v = data[key]
        self._loading = False

    def _save(self):
        if self._loading or self._db is None:
            return
        try:
            self._db.set("android_prefs", json.dumps(self.to_dict()))
        except Exception:
            pass

    def to_dict(self):
        return {getattr(self, n).key: getattr(self, n).value for n in DEFAULTS}

    def from_dict(self, d):
        self._loading = True
        for n in DEFAULTS:
            p = getattr(self, n)
            if p.key in d:
                p._v = d[p.key]
        self._loading = False
        self._save()
        for f in list(_listeners):
            f("*")

    def listen(self, f):
        _listeners.append(f)

    def favSet(self):
        return {x for x in self.favourites.value.split("\n") if x.strip()}


Prefs = _Prefs()
