# Tiny job server on the pod, port 8000, every call needs the X-Job-Token header:
#   GET /log?name=N  (tail of N.log)   GET /file?name=PATH  (404 if missing; only inside JOB)
#   POST /upload?name=F  (body -> JOB/F)   POST /run?name=N  (body is a bash command run in JOB, output -> N.log)
import http.server, os, subprocess, urllib.parse
TOKEN = os.environ["JOB_TOKEN"]; JOB = os.environ.get("JOB_DIR", "/workspace/job"); os.makedirs(JOB, exist_ok=True)
PROCS = {}
class H(http.server.BaseHTTPRequestHandler):
    def _ok(self, body=b"ok", ctype="text/plain"):
        self.send_response(200); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def _auth(self):
        if self.headers.get("X-Job-Token") != TOKEN:
            self.send_response(403); self.end_headers(); return False
        return True
    def do_GET(self):
        if not self._auth(): return
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == "/log":
            n = q.get("name", ["run"])[0]; p = f"{JOB}/{os.path.basename(n)}.log"
            data = open(p, "rb").read()[-6000:] if os.path.exists(p) else b"(no log yet)"
            st = {k: (v.poll() if v else None) for k, v in PROCS.items()}
            return self._ok(f"status {st}\n".encode() + data)
        if u.path == "/file":
            p = os.path.realpath(os.path.join(JOB, q.get("name", [""])[0].lstrip("/")))
            if not p.startswith(os.path.realpath(JOB) + os.sep) or not os.path.isfile(p):
                self.send_response(404); self.send_header("Content-Length", "0"); self.end_headers(); return
            return self._ok(open(p, "rb").read(), "application/octet-stream")
        self._ok(b"alive")
    def do_POST(self):
        if not self._auth(): return
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if u.path == "/upload":
            p = os.path.join(JOB, os.path.basename(q["name"][0])); open(p, "wb").write(body); return self._ok(b"saved")
        if u.path == "/run":
            n = q.get("name", ["run"])[0]
            PROCS[n] = subprocess.Popen(["bash", "-c", body.decode()], cwd=JOB, stdout=open(f"{JOB}/{n}.log", "ab"), stderr=subprocess.STDOUT)
            return self._ok(b"started")
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
