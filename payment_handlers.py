"""
Admin to'lov tasdiqlash / rad etish handlerlari.

Bu modul python-telegram-bot (v20+, async) kutubxonasi uchun mo'ljallangan.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from config import (
    MONTHLY_FEE,
    CARD_NUMBER,
    ADMIN_ID,
    GROUP_CHAT_ID,
    SUBSCRIPTION_DAYS,
)
from models import Driver
# Eslatma: 'database.py' faylingizdan session import qiling.
try:
    from database import session
except ImportError:
    session = None

logger = logging.getLogger(__name__)


async def send_payment_request_to_admin(
    context: ContextTypes.DEFAULT_TYPE,
    driver: Driver,
    photo_file_id: str,
    driver_full_info: str,
):
    """
    Haydovchining to'lov chekini (rasm) va to'liq ma'lumotlarini Admin paneliga
    inline tugmalar bilan yuboradi.

    :param context: telegram.ext Context
    :param driver: Driver model obyekti
    :param photo_file_id: yuborilgan rasmning file_id si
    :param driver_full_info: haydovchining to'liq ma'lumotlari (ism, telefon, h.k.)
    """
    if session is None:
        logger.error("database session import qilinmagan!")
        return

    if not ADMIN_ID:
        logger.error("ADMIN_ID sozlanmagan! config.py ni tekshiring.")
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ To'lovni tasdiqlash va faollashtirish",
                callback_data=f"confirm_payment:{driver.id}",
            ),
            InlineKeyboardButton(
                "❌ To'lovni rad etish",
                callback_data=f"reject_payment:{driver.id}",
            ),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    caption = (
        f"💰 To'lov cheki keldi!\n\n"
        f"👤 Haydovchi ID: {driver.id}\n"
        f"📱 Telegram ID: {driver.telegram_id}\n"
        f"💳 Summa: {MONTHLY_FEE:,} so'm\n\n"
        f"{driver_full_info}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=caption,
        reply_markup=reply_markup,
    )


async def confirm_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("Siz admin emassiz!", show_alert=True)
        return

    try:
        driver_id = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("Noto'g'ri callback ma'lumoti.")
        return

    if session is None:
        await query.edit_message_text("Baza sessiyasi kiritilmagan!")
        return

    driver = session.query(Driver).get(driver_id)
    if not driver:
        await query.edit_message_text(f"Haydovchi topilmadi (ID: {driver_id}).")
        return

    driver.confirm_payment()
    session.commit()

    invite_link_text = "Guruhga kirish havolasi mavjud emas."
    if GROUP_CHAT_ID:
        try:
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=GROUP_CHAT_ID,
                member_limit=1,
                name=f"Driver {driver.id}",
            )
            invite_link_text = invite_link.invite_link
        except Exception as e:
            logger.error(f"Invite link yaratishda xatolik: {e}")
            invite_link_text = "Guruhga kirish havolasi yaratilmadi."

    if driver.telegram_id:
        await context.bot.send_message(
            chat_id=driver.telegram_id,
            text=(
                "Sizning to'lovingiz tasdiqlandi! "
                f"{SUBSCRIPTION_DAYS} kunlik obuna faollashdi. "
                "Quyidagi havola orqali haydovchilar guruhiga qo'shiling:\n"
                f"{invite_link_text}"
            ),
        )

    await query.edit_message_text(
        text=(
            f"{query.message.text}\n\n"
            f"✅ To'lov tasdiqlandi va obuna faollashtirildi "
            f"(Haydovchi ID: {driver_id})."
        )
    )


async def reject_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer("Siz admin emassiz!", show_alert=True)
        return

    try:
        driver_id = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("Noto'g'ri callback ma'lumoti.")
        return

    if session is None:
        await query.edit_message_text("Baza sessiyasi kiritilmagan!")
        return

    driver = session.query(Driver).get(driver_id)
    if not driver:
        await query.edit_message_text(f"Haydovchi topilmadi (ID: {driver_id}).")
        return

    driver.payment_status = "unpaid"
    driver.is_verified = False
    session.commit()

    if driver.telegram_id:
        await context.bot.send_message(
            chat_id=driver.telegram_id,
            text=(
                "To'lov tasdiqlanmadi. "
                "Iltimos, chekni qaytadan tekshirib yuboring yoki admin bilan bog'laning."
            ),
        )

    await query.edit_message_text(
        text=(
            f"{query.message.text}\n\n"
            f"❌ To'lov rad etildi (Haydovchi ID: {driver_id})."
        )
    )


payment_admin_handlers = [
    CallbackQueryHandler(
        confirm_payment_handler, pattern=r"^confirm_payment:\d+$"
    ),
    CallbackQueryHandler(
        reject_payment_handler, pattern=r"^reject_payment:\d+$"
    ),
]