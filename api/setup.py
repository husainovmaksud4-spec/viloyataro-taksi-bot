import os
import urllib.request
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        token = os.environ.get("BOT_TOKEN", "")
        url = "https://viloyataro-taksi-bot-c5hu.vercel.app/api/webhook"
        api_url = f"https://telegram.org{token}/setWebhook?url={url}"
        req = urllib.request.urlopen(api_url)
        res = req.read()
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(res)
