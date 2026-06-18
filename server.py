#!/usr/bin/env python3
import http.server
import json
import urllib.request
import os
import ssl

PORT = 9000
TOKEN_FILE = "/root/.github_token"
GITHUB_TOKEN = ""
if os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE) as f:
        GITHUB_TOKEN = f.read().strip()
if not GITHUB_TOKEN:
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/github/"):
            return self.handle_github()
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def handle_github(self):
        if not GITHUB_TOKEN:
            self.send_error(503, "GitHub token not configured")
            return
        endpoint = self.path.replace("/api/github/", "", 1)
        req = urllib.request.Request(f"https://api.github.com/{endpoint}")
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("User-Agent", "NeuroSetu-Dashboard")
        try:
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, context=ctx, timeout=15)
            data = json.loads(resp.read().decode())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            err = json.dumps({"error": str(e.code), "reason": str(e.reason)})
            self.wfile.write(err.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, fmt, *args):
        if "/api/" not in args[0]:
            super().log_message(fmt, *args)


if __name__ == "__main__":
    os.chdir(STATIC_DIR)
    srv = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serving NeuroSetu Dashboard on http://0.0.0.0:{PORT}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()
