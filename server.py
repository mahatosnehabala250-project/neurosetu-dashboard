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
SUPABASE_REF = "nwtssbqfnilxeufgopfg"
SUPABASE_ANON_KEY = ""
SUPABASE_SERVICE_KEY = ""
ANON_FILE = "/root/.supabase_anon_key"
SERVICE_FILE = "/root/.supabase_service_key"
if os.path.exists(ANON_FILE):
    with open(ANON_FILE) as f:
        SUPABASE_ANON_KEY = f.read().strip()
if os.path.exists(SERVICE_FILE):
    with open(SERVICE_FILE) as f:
        SUPABASE_SERVICE_KEY = f.read().strip()
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith('.html'):
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/api/github/"):
            return self.handle_github()
        if self.path == "/api/supabase-config":
            return self.handle_supabase_config()
        if self.path.startswith("/api/supabase/"):
            return self.handle_supabase()
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/supabase/"):
            return self.handle_supabase()
        self.send_error(405)

    def do_PATCH(self):
        if self.path.startswith("/api/supabase/"):
            return self.handle_supabase()
        self.send_error(405)

    def do_DELETE(self):
        if self.path.startswith("/api/supabase/"):
            return self.handle_supabase()
        self.send_error(405)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, apikey, Authorization")
        self.end_headers()

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

    def handle_supabase_config(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        config = {
            "ref": SUPABASE_REF,
            "anon_key": SUPABASE_ANON_KEY,
            "url": f"https://{SUPABASE_REF}.supabase.co"
        }
        self.wfile.write(json.dumps(config).encode())

    def handle_supabase(self):
        if not SUPABASE_SERVICE_KEY:
            self.send_error(503, "Supabase not configured")
            return
        method = self.command
        endpoint = self.path.replace("/api/supabase/", "", 1)
        url = f"https://{SUPABASE_REF}.supabase.co/rest/v1/{endpoint}"
        body = None
        if method in ("POST", "PATCH", "PUT"):
            length = int(self.headers.get("Content-Length", 0))
            if length:
                body = self.rfile.read(length)
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("apikey", SUPABASE_ANON_KEY)
        req.add_header("Authorization", f"Bearer {SUPABASE_SERVICE_KEY}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "NeuroSetu")
        try:
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, context=ctx, timeout=15)
            data = None
            content = resp.read().decode()
            if content.strip():
                data = json.loads(content)
            self.send_response(resp.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Expose-Headers", "*")
            self.end_headers()
            if data is not None:
                self.wfile.write(json.dumps(data).encode())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            err_body = e.read().decode()
            err = json.dumps({"error": str(e.code), "reason": str(e.reason), "detail": err_body})
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
