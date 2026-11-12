import json, asyncio, os, sys, traceback
from http.server import BaseHTTPRequestHandler
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import BOT_TOKEN, MONTHLY_FEE, CARD_NUMBER, CARD_HOLDER
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from payment_handlers import send_payment_request_to_admin, confirm_payment_handler, reject_payment_handler

async def start(d, u):
    kb = [[InlineKeyboardButton("\u1f4b3 Obuna boshlash / To'lov qilish", callback_data="pay_info")]]
    await d.message.reply_text("Assalomu alaykum! Viloyatlararo taksi guruhiga ulanish uchun oylik obuna to'lov tizimiga xush keliblisiz!\n\nTo'lovqo o'tish uchun pastdagi tugmani bosing:", reply_markup=InlineKeyboardMarkup(kb))

async def pay_info(d, u):
    q = d.callback_query
    await q.answer()
    txt = f"\u1f4b3 Oylik obuna to'lovi: {MONTHLY_FEE} so'm\n\u1f4b3 Karta raqami: {CARD_NUMBER}\n\u1f464 Karta egasi: {CARD_HOLDER}\n\nTo'lovqo qilganingizdan so'ng, chek rasmini shu botga yuboring."
    await q.message.edit_text(txt)

async def photo_handler(d, u):
    photo = d.message.photo[-1].file_id
    await send_payment_request_to_admin(d, u, photo)

async def process(data):
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(pay_info, pattern="^pay_info$"))
    app.add_handler(CallbackQueryHandler(confirm_payment_handler, pattern="^confirm_"))
    app.add_handler(CallbackQueryHandler(reject_payment_handler, pattern="^reject_"))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    await app.initialize()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    await app.shutdown()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
            asyncio.run(process(data))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{\"ok\":true}")
        except Exception as e:
            print(traceback.format_exc())
            self.send_response(200)
            self.end_headers()
            self.wfile.write(str(e).encode())
