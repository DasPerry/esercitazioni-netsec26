from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse, json, re, threading

NOTES = {}
NEXT_ID = 1
LOCK = threading.Lock()
NOTE_RE = re.compile(r"/notes/([0-9]+)")

class MiniAPIHandler(BaseHTTPRequestHandler):

    def _send(self, status, payload=None, allow=None):
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        if payload is not None:
            self.send_header("Content-Type", "application/json")
        if allow:
            self.send_header("Allow", allow)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if status != 204:
            self.wfile.write(body)

    def _read_body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return None
        if n < 0:
            return None
        return self.rfile.read(n)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/":
            return self._send(200)
        if u.path == "/echo":
            q = urllib.parse.parse_qs(u.query, keep_blank_values=True)
            return self._send(200, {"msg": q.get("msg", [""])[0]})
        m = NOTE_RE.fullmatch(u.path)
        if m:
            nid = int(m.group(1))
            with LOCK:
                text = NOTES.get(nid)
            if text is None:
                return self._send(404)
            return self._send(200, {"id": nid, "text": text})
        self._send(404)

    def do_POST(self):
        body = self._read_body()          # sempre letto prima di rispondere
        path = urllib.parse.urlparse(self.path).path
        if path != "/notes":
            return self._send(404)
        if body is None:
            return self._send(400)
        if self.headers.get_content_type() != "application/json":
            return self._send(415)
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._send(400)
        if not isinstance(data, dict) or not isinstance(data.get("text"), str):
            return self._send(400)
        global NEXT_ID
        with LOCK:
            nid = NEXT_ID
            NEXT_ID += 1
            NOTES[nid] = data["text"]
        self._send(201, {"id": nid})

    def do_DELETE(self):
        m = NOTE_RE.fullmatch(urllib.parse.urlparse(self.path).path)
        if not m:
            return self._send(404)
        with LOCK:
            existed = NOTES.pop(int(m.group(1)), None) is not None
        self._send(204 if existed else 404)

    def _unsupported_method(self):
        self._read_body()  # svuota sempre il body prima di rispondere
        path = urllib.parse.urlparse(self.path).path
        if path == "/notes":
            return self._send(405, allow="POST")
        if NOTE_RE.fullmatch(path):
            return self._send(405, allow="GET, DELETE")
        self._send(404)

    def __getattr__(self, name):
        # qualsiasi do_<METODO> non definito (PUT, PATCH, HEAD, OPTIONS, FOO...)
        if name.startswith("do_"):
            return self._unsupported_method
        raise AttributeError(name)


if __name__ == "__main__":
    print("Mini API in ascolto sulla porta 8080...")
    ThreadingHTTPServer(("0.0.0.0", 8080), MiniAPIHandler).serve_forever()
