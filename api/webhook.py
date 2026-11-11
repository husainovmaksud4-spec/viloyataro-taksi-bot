"""
Telegram Bot webhook handler — Vercel serverless function.

Vercel POST so'rovlarini qabul qiladi va python-telegram-bot orqali
yangilanlarni (updates) qayta ishlaydi.
"""

import json
import asyncio
import os
import sys
from http.server import BaseHTTPRequestHandler

# Loyiha ildizini Python yo'liga qo'shamiz (config, models, payment_handlers va h.k.)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import BOT_TOKEN
from telegram import Update
from telegram.ext import Application

# Applicationni xotirada saqlab quyamiz (bir konteyner ichida qayta ishlatilishi mumkin)
_app = None


def get_application():
    global _app
    if _app is None:
        if not BOT_TOKEN:
            raise RuntimeError("BOT_TOKEN sozlanmagan! .env yoki Vercel Environment Variables ni tekshiring.")
        _app = Application.builder().token(BOT_TOKEN).build()

        # Admin to'lov handlerlarini ro'yxatdan o'tkazamiz
        from payment_handlers import payment_admin_handlers
        for handler in payment_admin_handlers:
            _app.add_handler(handler)

    return _app


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            if not body:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error": "empty body"}')
                return

            update_data = json.loads(body)
            app = get_application()

            update = Update.de_json(update_data, app.bot)
            asyncio.run(app.process_update(update))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "webhook active"}).encode())