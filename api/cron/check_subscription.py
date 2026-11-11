"""
Vercel Cron endpoint — obuna muddati tugagan haydovchini tekshiradi.

Vercel Cron `vercel.json` da ko'rsatilgan schedule bo'yicha shu endpointni
avtomatik chaqiradi. Har kuni 1 marta (00:00 UTC) ishlaydi.
"""

import asyncio
import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Loyiha ildizini Python yo'liga qo'shamiz
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from config import BOT_TOKEN, CRON_SECRET
from subscription_checker import check_expired_subscriptions
from telegram import Bot


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Cron kalitini tekshiramiz (ixtiyoriy, lekin tavsiya etiladi)
        if CRON_SECRET:
            auth_header = self.headers.get("Authorization", "")
            if auth_header != f"Bearer {CRON_SECRET}":
                self.send_response(401)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "unauthorized"}).encode())
                return

        async def _run():
            bot = Bot(token=BOT_TOKEN)
            try:
                await check_expired_subscriptions(bot)
            finally:
                await bot.close()

        try:
            asyncio.run(_run())
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {"status": "ok", "message": "subscription check completed"}
                ).encode()
            )
        except Exception as exc:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps({"status": "error", "message": str(exc)}).encode()
            )

    def do_POST(self):
        self.do_GET()