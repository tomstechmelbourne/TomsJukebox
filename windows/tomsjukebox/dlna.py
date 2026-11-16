"""Play to TV / Wi-Fi speaker (DLNA / UPnP AV). Finds renderers on the home network, serves the
song from this computer over a small local web server, and controls play / pause / stop / volume.
Only works inside the home network; nothing goes to the internet."""
import html
import mimetypes
import os
import re
import socket
import threading
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .app_info import log

ST = "urn:schemas-upnp-org:service:AVTransport:1"
AVT = "urn:schemas-upnp-org:service:AVTransport:1"
RC = "urn:schemas-upnp-org:service:RenderingControl:1"


def discover(timeout=3.0):
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\n"
           f"MX: 2\r\nST: {ST}\r\n\r\n").encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    s.settimeout(timeout)
    locs = set()
    try:
        s.sendto(msg, ("239.255.255.250", 1900))
        s.sendto(msg, ("239.255.255.250", 1900))
        while True:
            data, _addr = s.recvfrom(65507)
            m = re.search(rb"(?im)^location:\s*(\S+)", data)
            if m:
                locs.add(m.group(1).decode())
    except socket.timeout:
        pass
    except OSError as e:
        log.info("ssdp failed: %s", e)
    finally:
        s.close()
    out = []
    for loc in locs:
        try:
            out.append(Renderer.from_location(loc))
        except Exception as e:
            log.info("renderer %s unusable: %s", loc, e)
    return [r for r in out if r and r.avt_url]


def _strip_ns(tag):
    return tag.split("}", 1)[-1]


class Renderer:
    def __init__(self, name, avt_url, rc_url, host):
        self.name, self.avt_url, self.rc_url, self.host = name, avt_url, rc_url, host

    @classmethod
    def from_location(cls, loc):
        with urllib.request.urlopen(loc, timeout=4) as r:
            root = ET.fromstring(r.read())
        name, avt, rc = "Renderer", None, None
        for el in root.iter():
            t = _strip_ns(el.tag)
            if t == "friendlyName" and name == "Renderer":
                name = (el.text or name).strip()
            if t == "service":
                kids = {_strip_ns(c.tag): (c.text or "").strip() for c in el}
                if kids.get("serviceType", "").startswith("urn:schemas-upnp-org:service:AVTransport"):
                    avt = urllib.parse.urljoin(loc, kids.get("controlURL", ""))
                if kids.get("serviceType", "").startswith("urn:schemas-upnp-org:service:RenderingControl"):
                    rc = urllib.parse.urljoin(loc, kids.get("controlURL", ""))
        return cls(name, avt, rc, urllib.parse.urlparse(loc).hostname)

    def _soap(self, url, service, action, args):
        body = "".join(f"<{k}>{html.escape(str(v))}</{k}>" for k, v in args)
        env = ('<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" '
               's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><s:Body>'
               f'<u:{action} xmlns:u="{service}">{body}</u:{action}></s:Body></s:Envelope>').encode("utf-8")
        req = urllib.request.Request(url, data=env, headers={
            "Content-Type": 'text/xml; charset="utf-8"', "SOAPACTION": f'"{service}#{action}"'})
        with urllib.request.urlopen(req, timeout=6) as r:
            return r.read().decode("utf-8", "replace")

    def play_url(self, url, title="", artist="", mime="audio/mpeg"):
        meta = ('<DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dc="http://purl.org/dc/elements/1.1/" '
                'xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"><item id="1" parentID="0" restricted="1">'
                f'<dc:title>{html.escape(title)}</dc:title><dc:creator>{html.escape(artist)}</dc:creator>'
                '<upnp:class>object.item.audioItem.musicTrack</upnp:class>'
                f'<res protocolInfo="http-get:*:{mime}:*">{html.escape(url)}</res></item></DIDL-Lite>')
        self._soap(self.avt_url, AVT, "SetAVTransportURI", [("InstanceID", 0), ("CurrentURI", url), ("CurrentURIMetaData", meta)])
        self._soap(self.avt_url, AVT, "Play", [("InstanceID", 0), ("Speed", 1)])

    def pause(self):
        self._soap(self.avt_url, AVT, "Pause", [("InstanceID", 0)])

    def resume(self):
        self._soap(self.avt_url, AVT, "Play", [("InstanceID", 0), ("Speed", 1)])

    def stop(self):
        try:
            self._soap(self.avt_url, AVT, "Stop", [("InstanceID", 0)])
        except Exception:
            pass

    def set_volume(self, v):
        if self.rc_url:
            self._soap(self.rc_url, RC, "SetVolume", [("InstanceID", 0), ("Channel", "Master"), ("DesiredVolume", int(v))])

    def position(self):
        x = self._soap(self.avt_url, AVT, "GetPositionInfo", [("InstanceID", 0)])
        m = re.search(r"<RelTime>(\d+):(\d+):(\d+)", x)
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)) if m else 0


class MediaServer:
    """Tiny web server that lets the TV fetch the current song from this computer (supports Range)."""

    def __init__(self):
        self.files = {}
        srv = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_HEAD(self):
                self._serve(head=True)

            def do_GET(self):
                self._serve()

            def _serve(self, head=False):
                key = self.path.strip("/").split(".")[0]
                path = srv.files.get(key)
                if not path or not os.path.exists(path):
                    self.send_error(404)
                    return
                size = os.path.getsize(path)
                start, end = 0, size - 1
                rng = self.headers.get("Range")
                if rng:
                    m = re.match(r"bytes=(\d*)-(\d*)", rng)
                    if m:
                        if m.group(1):
                            start = int(m.group(1))
                        if m.group(2):
                            end = int(m.group(2))
                    self.send_response(206)
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                else:
                    self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(path)[0] or "audio/mpeg")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(end - start + 1))
                self.send_header("transferMode.dlna.org", "Streaming")
                self.end_headers()
                if head:
                    return
                with open(path, "rb") as fh:
                    fh.seek(start)
                    left = end - start + 1
                    try:
                        while left > 0:
                            chunk = fh.read(min(65536, left))
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            left -= len(chunk)
                    except (ConnectionError, OSError):
                        pass

        self.httpd = ThreadingHTTPServer(("0.0.0.0", 0), H)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url_for(self, path, renderer_host):
        key = uuid.uuid4().hex[:12]
        self.files[key] = path
        ext = os.path.splitext(path)[1].lower()
        return f"http://{local_ip(renderer_host)}:{self.port}/{key}{ext}"

    def close(self):
        self.httpd.shutdown()


def local_ip(target="192.168.1.1"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target or "192.168.1.1", 9))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def mime_for(path):
    return mimetypes.guess_type(path)[0] or {"flac": "audio/flac", "m4a": "audio/mp4", "opus": "audio/ogg"}.get(
        os.path.splitext(path)[1][1:].lower(), "audio/mpeg")
