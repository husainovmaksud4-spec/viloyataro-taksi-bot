import os
from datetime import timedelta

# =============================================================================
# Asosiy sozlamalar
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
SQLALCHEMY_DATABASE_URI = os.getenv(
    "DATABASE_URL", "sqlite:///drivers.db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# =============================================================================
# Oylik obuna (to'lov) sozlamalari
# =============================================================================

# Haydovchining to'lash kerak bo'lgan oylik obuna summasi (so'm)
MONTHLY_FEE = 200000

# Admin qabul qiluvchi plastik karta raqami (foydalanuvchi to'lov qilish uchun)
CARD_NUMBER = "XXXX XXXX XXXX XXXX"

# Obuna muddati (kun) — to'lov tasdiqlaganda subscription_ends_at ga qo'shiladi
SUBSCRIPTION_DAYS = 30

# =============================================================================
# Bot sozlamalari
# =============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://viloyataro-taksi-bot-ov76.vercel.app")  # Masalan: https://proyekt.vercel.app/webhook

# =============================================================================
# Admin sozlamalari
# =============================================================================

# Adminning Telegram ID si (faqat u tasdiqlash/rad etish tugmalarini bosishi mumkin)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Haydovchilar guruhining chat ID si (guruhga kirish havolasi yaratish uchun)
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))

# Vercel Cron uchun kalit (cron chaqirganda Authorization: Bearer <CRON_SECRET>)
CRON_SECRET = os.getenv("CRON_SECRET", "")