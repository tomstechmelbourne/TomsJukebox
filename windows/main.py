"""Tom's Jukebox - start here.  python main.py [--demo] [--selftest]"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

for _s in (sys.stdout, sys.stderr):  # Vietnamese text must never crash a Windows console
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from tomsjukebox import app_info  # noqa: E402


def _excepthook(etype, value, tb):
    text = "".join(traceback.format_exception(etype, value, tb))
    app_info.log.error("unhandled error:\n%s", text)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.warning(None, app_info.APP_NAME,
                                f"{value}\n\nLog: {app_info.data_dir() / 'TomsJukebox.log'}")
    except Exception:
        pass


def main():
    app_info.setup_logging()
    if "--selftest" in sys.argv:
        from tomsjukebox import selftest
        sys.exit(selftest.run())
    sys.excepthook = _excepthook
    from tomsjukebox import winint
    winint.set_app_id()
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication, QSplashScreen
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(app_info.APP_NAME)
    app.setOrganizationName(app_info.BRAND)
    app.setWindowIcon(QIcon(app_info.asset("app_icon_256.png")))
    app.setStyle("Fusion")
    from tomsjukebox.db import DB
    from tomsjukebox import i18n
    db = DB()
    i18n.set_lang(db.get("lang"))
    from tomsjukebox.ui import dialogs
    from tomsjukebox.art.prefs import Prefs
    Prefs.bind(db)
    dpr = app.primaryScreen().devicePixelRatio() if app.primaryScreen() else 1.0
    holder = {}
    if Prefs.splashOn.value:
        from tomsjukebox.ui.splashfx import AnimatedSplash
        splash = AnimatedSplash(dpr, lambda: holder["win"].show())
    else:
        splash = QSplashScreen(dialogs.splash_pixmap(dpr))
    splash.show()
    app.processEvents()
    if app_info.DEMO and not db.q("SELECT id FROM folders"):
        from tomsjukebox import demo, scanner
        folder = str(app_info.data_dir() / "DemoMusic")
        demo.make_library(folder)
        scanner.add_folder(db, folder)
        scanner.scan(db)
    from tomsjukebox.ui.main_window import MainWindow
    win = MainWindow(db)
    holder["win"] = win
    if hasattr(splash, "finish_when_ready"):
        splash.finish_when_ready()
    else:
        QTimer.singleShot(900, lambda: (win.show(), splash.finish(win)))
    code = app.exec()
    db.close()
    sys.exit(code)


if __name__ == "__main__":
    main()
