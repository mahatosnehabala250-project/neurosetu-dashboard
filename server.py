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
        endpoint = self.path.replace("/api/supabase/", "", 1)
        url = f"https://{SUPABASE_REF}.supabase.co/rest/v1/{endpoint}"
        req = urllib.request.Request(url)
        req.add_header("apikey", SUPABASE_ANON_KEY)
        req.add_header("Authorization", f"Bearer {SUPABASE_SERVICE_KEY}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "NeuroSetu")
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
