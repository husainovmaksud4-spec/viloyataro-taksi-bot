# Drivers oylik obuna (to'lov) tizimi

Ushbu papkada `Drivers` (haydovchilar) jadvalini oylik obuna to'lov tizimi uchun
yangilash kerak bo'lgan fayllar toplangan.

## Qo'shilgan maydonlar (`drivers` jadvali)

| Maydon | Tur | Default / noto'g'ri | Izoh |
|--------|-----|---------------------|------|
| `payment_status` | `String(20)` | `'unpaid'` | `'unpaid'` — to'lanmagan, `'pending'` — kutilmoqda, `'paid'` — to'langan |
| `subscription_ends_at` | `DateTime` (nullable) | `NULL` | To'lov tasdiqlangach `hozirgi vaqt + 30 kun` sifatida saqlanadi |
| `is_verified` | `Boolean` | `False` | Admin to'lovni tasdiqlaganmi? |
| `telegram_id` | `BigInteger` | `NULL` | Haydovchining Telegram ID si |

## config.py qo'shimchalar

```python
MONTHLY_FEE = 200000          # oylik obuna summasi (so'm)
CARD_NUMBER = "XXXX XXXX XXXX XXXX"  # admin karta raqami
SUBSCRIPTION_DAYS = 30        # obuna muddati (kun)
ADMIN_ID = 123456789          # adminning Telegram ID si
GROUP_CHAT_ID = -1001234567890  # haydovchilar guruhining chat ID si
```

## To'lovni tasdiqlash (misol)

```python
from models import Driver

driver = session.query(Driver).get(driver_id)
driver.confirm_payment()   # payment_status='paid', is_verified=True, subscription_ends_at = now + 30 kun
session.commit()

print(driver.is_subscription_active())  # True/False
```

## Adminga chek yuborish (bot)

`payment_handlers.py` da `send_payment_request_to_admin(...)` funksiyasi bor.
U haydovchining chek rasmini va to'liq ma'lumotlarini admin ID ga inline tugmalar bilan yuboradi:

- ✅ To'lovni tasdiqlash va faollashtirish
- ❌ To'lovni rad etish

## Bot dispatcher ga handlerlarni qo'shish (python-telegram-bot v20+)

```python
from telegram.ext import ApplicationBuilder
from payment_handlers import payment_admin_handlers

app = ApplicationBuilder().token("BOT_TOKEN").build()

for handler in payment_admin_handlers:
    app.add_handler(handler)

app.run_polling()
```

## Migratsiya qo'llash (Alembic)

```bash
alembic upgrade head
```

## Eslatma

- `database.py` faylingizdan `session` import qilinishi kerak (yoki boshqa nom bilan).
- Bot admin bo'lib bo'lgan guruhda `create_chat_invite_link` chaqirishi uchun
  botning guruhda admin huquqi bo'lishi kerak.
- Agar sizda allaqachon mavjud `drivers` jadvali va model bo'lsa, yuqori kodlarni
  mavjud loyihangizga nusxalay olasiz. SQLAlchemy'dan tashqari ORM (Django, SQLModel)
  foydalanilasay, maydon turlari va default qiymatlarni moslashtiring.


## Fon tekshiruv (obuna muddati tugagandan so'ng)

`subscription_checker.py` faylida quyidagi funksiyalar mavjud:

- `check_expired_subscriptions(bot)` — muddati o'tgan va `payment_status='paid'` bo'lgan
  barcha haydovchini topadi, ularni `payment_status='unpaid'`, `is_verified=False` ga
  o'zgartiradi, guruhdan chiqaradi va shaxsiy chatga ogohlantirish yuboradi.
- `start_scheduler(bot, interval_hours=24)` — APScheduler orqali tekshiruvni
  berilgan soat oralig'ida ishga tushiradi.
- `run_periodic_check(bot, interval_seconds=86400)` — asyncio tsiklida doimiy
  tekshiruv (APScheduler o'rnatilmagan bo'lsa).

### Botga ulash (python-telegram-bot v20+)

```python
from telegram.ext import ApplicationBuilder
from subscription_checker import start_scheduler

app = ApplicationBuilder().token("BOT_TOKEN").build()

# Fon tekshiruvni har 24 soatda bir marta ishga tushirish
scheduler = start_scheduler(app.bot, interval_hours=24)

app.run_polling()
```

### Talab qilinadigan kutubxona

```bash
pip install apscheduler
```

### Eslatma

- Bot haydovchilar guruhida **admin huquqi**ga ega bo'lishi kerak (`ban_chat_member` uchun).
- `config.py` da `GROUP_CHAT_ID` to'g'ri sozlanishi kerak.


## Vercel'ga deploy (Webhook + Cron)

### 1. Loyihani GitHub'ga yuklang
Barcha fayllarni (mulloqat `api/`, `vercel.json`, `requirements.txt` h.k.) GitHub repositoriyasiga push qiling.

### 2. Vercel'ga ulang
- [vercel.com](https://vercel.com) saytiga kiring
- GitHub repositoriyangizni import qiling
- Framework o'rniga **Other** ni tanlang
- Build sozlamalarini `vercel.json` orqali boshqaramiz

### 3. Environment Variables sozlang
Vercel dashboard → **Settings → Environment Variables** bo'limiga quyidagini kiriting:

| Kalit | Qiymat |
|-------|--------|
| `BOT_TOKEN` | Telegram bot tokeni (`@BotFather` dan olingan) |
| `WEBHOOK_URL` | `https://sizning-proyekt.vercel.app/webhook` |
| `ADMIN_ID` | Adminning Telegram ID raqami |
| `GROUP_CHAT_ID` | Haydovchilar guruhining chat ID si |
| `CRON_SECRET` | Cron chaqirish uchun sirli kalit (ixtiyoriy) |
| `DATABASE_URL` | Uzoq ma'lumotlar bazasi URL'i (PostgreSQL, Neon, Supabase h.k.) |

⚠️ **Eslatma:** Vercel serverless fayl tizimi faqat o'qish uchun bo'lgani uchun **SQLite foydalanib bo'lmaydi**. `DATABASE_URL` orqali uzoq PostgreSQL bazaga ulanishingiz kerak.

### 4. Webhook ni o'rnang
Deploy bo'lgandan so'ng, botga webhook ni sozlash uchun quyidagi URL ni brauzerda yoki `curl` orqali oching:

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
     -d "url=https://sizning-proyekt.vercel.app/webhook"
```

### 5. Vercel Cron
`vercel.json` da allaqachon sozlangan:

```json
"crons": [
  { "path": "/api/cron/check_subscription", "schedule": "0 0 * * *" }
]
```

Bu har kuni 00:00 UTC da `check_expired_subscriptions` funksiyasini chaqiradi. Agar `CRON_SECRET` sozlangan bo'lsa, Vercel avtomatik `Authorization: Bearer <CRON_SECRET>` headerini qo'shmaydi, shuning uchun cron endpointda tekshiruv qo'yilgan. Agar Vercel'dan custom header yuborilmasa, `CRON_SECRET` ni bo'sh qoldinga qoling yoki Vercel Cron sozlamalarida header qo'shing.

### Papka struktura
```
drivers_subscription/
├── vercel.json
├── requirements.txt
├── .env.example
├── config.py
├── models.py
├── payment_handlers.py
├── subscription_checker.py
├── README.md
├── api/
│   ├── __init__.py
│   └── webhook.py
└── api/cron/
    ├── __init__.py
    └── check_subscription.py
```