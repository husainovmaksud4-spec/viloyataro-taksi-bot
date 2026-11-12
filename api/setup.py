import os, urllib.request
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        t = os.environ.get("BOT_TOKEN", "").strip()
        u = "https://viloyataro-taksi-bot-c5hu.vercel.app/api/webhook"
        try:
            r = urllib.request.urlopen(f"https://api.telegram.org/bot{t}/setWebhook?url={u}")
            self.wfile.write(r.read())
        except Exception as e:
            self.wfile.write(str(e).encode())
