"""--selftest: opens the program in a temporary data folder, makes one of each output and exits 0 / 1.
Checks: demo library in 4 formats, scan, tags, covers, playback (silent output), gapless hand-over,
equaliser, backup + restore zip, M3U export/import, smart playlists, duplicates, fake-FLAC check,
radio recording from a local test stream (original + FLAC), state-from-location, all windows and looks."""
import os
import shutil
import sys
import tempfile
import threading
import time
import traceback


def run():
    tmp = tempfile.mkdtemp(prefix="tomsjukebox_selftest_")
    os.environ["TOMSJUKEBOX_DATA"] = os.path.join(tmp, "data")
    results = []

    def step(name, fn):
        t0 = time.time()
        try:
            fn()
            results.append((name, True, f"{time.time() - t0:.1f}s"))
            print(f"[OK]   {name}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"[FAIL] {name}: {e}")
            traceback.print_exc()

    from . import app_info, backup, db as dbm, demo, engine, radio, recorder, scanner, tags, tools
    db = dbm.DB()
    music = os.path.join(tmp, "music")
    ctx = {}

    def t_demo():
        ctx["files"] = demo.make_library(music, seconds=8)
        assert len(ctx["files"]) >= 10

    def t_scan():
        scanner.add_folder(db, music)
        a, u, r, off = scanner.scan(db)
        assert a == len(ctx["files"]), (a, len(ctx["files"]))
        n = db.one("SELECT COUNT(DISTINCT codec) c FROM tracks")["c"]
        assert n >= 4, n
        a2, _u, _r, _o = scanner.scan(db)
        assert a2 == 0

    def t_tags():
        p = ctx["files"][0]
        from PIL import Image
        import io
        im = Image.new("RGB", (300, 300), (14, 136, 170))
        buf = io.BytesIO()
        im.save(buf, "JPEG")
        tags.write(p, {"title": "Đổi Tên Thử", "year": 2025}, cover=buf.getvalue())
        info = tags.read(p)
        assert info["title"] == "Đổi Tên Thử" and info["year"] == 2025 and info["has_art"]
        assert tags.cover_bytes(p)

    def t_play():
        e = engine.Engine(null_output=True, fast=True)
        e.set_eq(True, engine.EQ_PRESETS["rock"])
        srcs = [engine.AVSource(ctx["files"][1]), engine.AVSource(ctx["files"][2])]
        state = {"given": False}

        def nxt():
            if state["given"]:
                return None
            state["given"] = True
            return (2, srcs[1], -3.0)
        e.next_provider = nxt
        e.play(1, srcs[0], 0.0)
        evs = []
        t0 = time.time()
        while time.time() - t0 < 20:
            evs += e.events()
            if ("ended", 2) in evs:
                break
            time.sleep(0.02)
        e.close()
        assert ("started", 1) in evs and ("started", 2) in evs, evs

    def t_backup():
        z = backup.make(db)
        assert os.path.getsize(z) > 1000
        ctx["zip"] = z

    def t_m3u():
        rows = db.q("SELECT * FROM tracks")
        out = os.path.join(tmp, "test.m3u8")
        tools.export_m3u([(r, scanner.track_path(r)) for r in rows], out, "Test")
        back = tools.import_m3u(out)
        assert len(back) == len(rows)

    def t_smart():
        for _en, _vi, rules in tools.SMART_TEMPLATES:
            sql, args = tools.smart_sql(rules)
            db.q(sql, args)

    def t_dupes():
        src = ctx["files"][3]
        dst = os.path.join(music, "copy_" + os.path.basename(src))
        shutil.copy(src, dst)
        scanner.scan(db)
        groups = tools.find_duplicates(db)
        assert any(len(g) >= 2 for g in groups)

    def t_fake_flac():
        mp3 = [f for f in ctx["files"] if f.endswith(".mp3")][0]
        import av
        import numpy as np
        # real full-band FLAC: white noise
        real = os.path.join(tmp, "real.flac")
        noise = (np.random.RandomState(1).randn(44100 * 25) * 0.1).astype(np.float32)
        demo.write_audio(real, noise, "flac")
        k_real = tools.lossy_cutoff_khz(real)
        # fake: noise -> MP3 128k -> FLAC
        lossy = os.path.join(tmp, "lossy.mp3")
        c = av.open(lossy, "w")
        s = c.add_stream("libmp3lame", rate=44100)
        s.layout = "stereo"
        s.bit_rate = 128000
        c.close()
        demo.write_audio(lossy, noise, "libmp3lame")
        dec = []
        ic = av.open(lossy)
        rs = av.AudioResampler(format="flt", layout="mono", rate=44100)
        for fr in ic.decode(audio=0):
            for o in rs.resample(fr):
                dec.append(o.to_ndarray().reshape(-1))
        ic.close()
        fake = os.path.join(tmp, "fake.flac")
        demo.write_audio(fake, np.concatenate(dec), "flac")
        k_fake = tools.lossy_cutoff_khz(fake)
        print(f"       cutoff real={k_real} kHz fake={k_fake} kHz ({os.path.basename(mp3)})")
        assert k_real and k_real > 19.5 and k_fake and k_fake < 19.0, (k_real, k_fake)

    def t_check():
        probs = tools.check_files(db, deep=True)
        assert isinstance(probs, list)

    def t_record():
        import http.server
        import socketserver
        mp3 = [f for f in ctx["files"] if f.endswith(".mp3")][0]
        data = open(mp3, "rb").read()

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("icy-name", "Test FM")
                self.end_headers()
                try:
                    for i in range(0, len(data), 4096):
                        self.wfile.write(data[i:i + 4096])
                        time.sleep(0.002)
                except Exception:
                    pass
        srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), H)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/stream"
        out = os.path.join(tmp, "rec")
        got = []
        for fmt in ("original", "flac", "mp3_320"):
            r = recorder.Recording("Test FM", url, out, fmt, seconds=3, on_file=got.append)
            r.start()
            r.join(timeout=30)
        srv.shutdown()
        assert len(got) >= 3, got
        for g in got:
            assert os.path.getsize(g) > 2048, g
        # the recorded files open and play
        for g in got:
            engine.AVSource(g)
        # radio stream through the ICY reader
        ctx["rec_files"] = got

    def t_state():
        assert radio.state_from_latlon(-37.81, 144.96) == "VIC"
        assert radio.state_from_latlon(-33.87, 151.21) == "NSW"
        assert radio.state_from_latlon(-31.95, 115.86) == "WA"

    def t_restore():
        z = ctx["zip"]
        db.x("DELETE FROM tracks")
        backup.restore(db, z)
        db2 = dbm.DB()
        assert db2.one("SELECT COUNT(*) c FROM tracks")["c"] > 0
        db2.close()

    for name, fn in (("demo library", t_demo), ("scan", t_scan), ("tags + cover", t_tags), ("playback + gapless + EQ", t_play),
                     ("backup zip", t_backup), ("m3u export/import", t_m3u), ("smart playlists", t_smart),
                     ("duplicates", t_dupes), ("fake FLAC check", t_fake_flac), ("check files", t_check),
                     ("radio recording", t_record), ("state from location", t_state)):
        step(name, fn)
    def t_art():
        """Every visualisation, skin, edge light, button set and record button draws without errors."""
        from PySide6.QtGui import QGuiApplication, QImage, QPainter, QColor
        app = QGuiApplication.instance()
        if app is None:
            from PySide6.QtWidgets import QApplication
            app = QApplication(["selftest"])
        ctx["app"] = app
        from .art.ds import DS, Color
        from .art.viz import drawViz
        from .art.skins import SkinList, paintSkin
        from .art.edge import drawEdge
        from .art.buttons import ButtonArt, RecArt, PLAY, REC
        from .art.themes import VizStyles, Motifs, EdgeEffects
        lv = [0.5] * 24
        cols = [Color(0xFFE8538A), Color(0xFF48B0C8), Color(0xFFFBB040)]
        img = QImage(200, 120, QImage.Format_ARGB32)
        n = 0
        for i in range(VizStyles.count()):
            img.fill(QColor(0, 0, 0))
            p = QPainter(img)
            drawViz(DS(p, 200, 120), i, 2.0, lv, cols)
            p.end()
            n += 1
        for k in SkinList.keys + ["m:%d" % i for i in range(len(Motifs.list))]:
            p = QPainter(img)
            paintSkin(DS(p, 200, 120), 1.0, 0.0, k)
            p.end()
        for e in range(len(EdgeEffects.names)):
            p = QPainter(img)
            drawEdge(DS(p, 200, 120), e, 1.0, 20, cols, 4, 1.0, 1.0)
            p.end()
        for b in range(len(ButtonArt.names)):
            p = QPainter(img)
            ButtonArt.draw(p, PLAY, b, 40, QColor("white"))
            p.end()
        for r in range(1, len(RecArt.names)):
            p = QPainter(img)
            RecArt.draw(p, False, r, 40, QColor("red"))
            RecArt.draw(p, True, r, 40, QColor("red"))
            p.end()
        assert n == 84, n

    def t_clip():
        from .ui.podtools import save_clip
        src = next(f for f in ctx["files"] if f.lower().endswith(".mp3"))
        dest = save_clip(db, src, "Tập Thử", "Podcast Thử", 1.0, 5.0)
        assert os.path.getsize(dest) > 1000, dest
        info = tags.read(dest) if hasattr(tags, "read") else None
        del info

    step("art: 84 visualisations, skins, edge lights, buttons", t_art)
    step("podcast A–B clip", t_clip)
    step("ui windows + looks", lambda: _ui(db, tmp))
    step("restore zip", t_restore)
    db.close()
    ok = all(r[1] for r in results)
    print("\nSELFTEST", "PASSED" if ok else "FAILED", f"({sum(r[1] for r in results)}/{len(results)})")
    app_info.log.info("selftest %s %s", "passed" if ok else "failed", results)
    if "--keep" not in sys.argv:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


def _ui(db, tmp):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)
    from .ui import dialogs, theme
    from .ui.main_window import MainWindow
    shots = None
    if "--shots" in sys.argv:
        shots = sys.argv[sys.argv.index("--shots") + 1]
        os.makedirs(shots, exist_ok=True)
    win = MainWindow(db, null_audio=True, fast_audio=False)
    win.show()

    def pump(ms=300):
        end = time.time() + ms / 1000
        while time.time() < end:
            app.processEvents()
            time.sleep(0.01)
    pump(800)
    rows = db.q("SELECT * FROM tracks WHERE kind='music' ORDER BY album, track_no")
    win.play_rows(rows, 0)
    pump(1500)
    assert win.player.current is not None
    for key in list(win.pages):
        win.go(key)
        pump(150)
    for d in (dialogs.SettingsDialog(win), dialogs.EQDialog(win), dialogs.AboutDialog(win), dialogs.MessagesDialog(win),
              dialogs.SmartDialog(win, None), dialogs.ScheduleDialog(win, db, None, None), dialogs.TagEditor(win, rows[:2])):
        d.show()
        pump(100)
        if shots:
            d.grab().save(os.path.join(shots, f"dlg_{type(d).__name__}.png"))
        d.close()
    dialogs.splash_pixmap(2.0)
    from .ui.miniplayer import MiniPlayer
    from .ui.picker import StylePicker, CATS
    from .ui.sleep import SleepDialog
    from .ui.dialogs2 import ShortcutsDialog
    for cat in CATS:
        d = StylePicker(win, cat)
        d.show()
        pump(60)
        if shots and cat in ("pack", "viz", "skin"):
            d.grab().save(os.path.join(shots, f"picker_{cat}.png"))
        d.close()
    for d in (SleepDialog(win), ShortcutsDialog(win)):
        d.show()
        pump(60)
        d.close()
    mini = MiniPlayer(win)
    mini.show()
    pump(100)
    mini.close()
    lang0, theme0 = db.get("lang"), db.get("theme")
    for lang in ("en", "vi"):
        win.set_lang(lang)
        for th in theme.ORDER:
            win.set_theme(th)
            for step in (0, 2):
                win.set_font_step(step)
                for page in (("songs", "albums", "radio", "now", "playlists", "recordings", "tools", "cd", "podcasts", "folders", "stats", "look")
                             if shots else ("songs", "now")):
                    win.go(page)
                    pump(250)
                    if shots and (lang == "vi" or page in ("songs", "now")):
                        win.grab().save(os.path.join(shots, f"{lang}_{th}_A{step}_{page}.png"))
    win.set_font_step(0)
    win.set_lang(lang0)
    win.set_theme(theme0)
    if shots:
        dialogs.splash_pixmap(1.0).save(os.path.join(shots, "splash.png"))
    QTimer.singleShot(0, win.close)
    pump(200)
    win.player.engine.close()
