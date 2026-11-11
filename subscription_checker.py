"""
Obuna muddati tugagan haydovchini avtomatik tekshiruvchi fon vazifa.

Ishlash tartibi:
  - APScheduler (yoki asyncio) orqali berilgan intervalda (masalan, har kuni 1 marta)
  - 'subscription_ends_at' < hozirgi vaqtdan oldin bo'lgan va payment_status='paid'
    bo'lgan barcha haydovchini topadi
  - Ularning payment_status='unpaid' va is_verified=False ga o'zgartiradi
  - Haydovchini haydovchilar guruhidan chiqaradi (ban_chat_member / kick_chat_member)
  - Shaxsiy chatga ogohlantirish xabar yuboridi
"""

import asyncio
import logging
from datetime import datetime, timezone

from telegram import Bot
from telegram.error import TelegramError, BadRequest

from config import GROUP_CHAT_ID, MONTHLY_FEE
from models import Driver


async def check_expired_subscriptions(bot: Bot):
    """
    Obuna muddati tugagan barcha haydovchini topib, ularni guruhdan chiqaradi
    va bazadagi holatini yangilaydi.

    :param bot: telegram.Bot obyekti
    """
    if session is None:
        logger.error("database session import qilinmagan!")
        return

    if not GROUP_CHAT_ID:
        logger.error("GROUP_CHAT_ID sozlanmagan! config.py ni tekshiring.")
        return

    now = datetime.now(timezone.utc)

    # 1. Muddati tugagan va to'lov qilingan bo'lgan haydovchini qidirish
    expired_drivers = (
        session.query(Driver)
        .filter(
            Driver.payment_status == "paid",
            Driver.subscription_ends_at.isnot(None),
            Driver.subscription_ends_at < now,
        )
        .all()
    )

    logger.info(f"Muddati tugagan haydovchilar soni: {len(expired_drivers)}")

    for driver in expired_drivers:
        try:
            # 2. Bazadagi holatni yangilash
            driver.payment_status = "unpaid"
            driver.is_verified = False
            session.commit()

            # 3. Guruhdan chiqarish (ban_chat_member / kick_chat_member)
            if driver.telegram_id:
                try:
                    await bot.ban_chat_member(
                        chat_id=GROUP_CHAT_ID,
                        user_id=driver.telegram_id,
                    )
                    # Agar foydalanuvchini faqat chiqarish kerak bo'lsa (ban dan keyin ochirish):
                    # await bot.unban_chat_member(
                    #     chat_id=GROUP_CHAT_ID,
                    #     user_id=driver.telegram_id,
                    # )
                    logger.info(f"Haydovchi guruhdan chiqarildi: {driver.telegram_id}")
                except BadRequest as e:
                    # Foydalanuvchi allaqachon guruhda yo'q yoki boshqa xatolik
                    logger.warning(
                        f"Guruhdan chiqarishda xatolik ({driver.telegram_id}): {e}"
                    )
                except TelegramError as e:
                    logger.error(f"Telegram xatosi ({driver.telegram_id}): {e}")

                # 4. Shaxsiy chatga ogohlantirish xabar yuborish
                try:
                    await bot.send_message(
                        chat_id=driver.telegram_id,
                        text=(
                            "⚠️ Sizning oylik obuna muddatingiz tugadi. "
                            f"Botdan foydalanish va guruhdagi buyurtmalarni ko'rishni "
                            f"davom ettirish uchun qaytadan {MONTHLY_FEE:,} so'm "
                            f"to'lovni amalga oshiring.\n\n"
                            f"Iltimos, to'lov chekini (skrinshot yoki rasm) shu yerga yuboring."
                        ),
                    )
                    logger.info(f"Ogohlantirish yuborildi: {driver.telegram_id}")
                except TelegramError as e:
                    logger.error(f"Xabar yuborishda xatolik ({driver.telegram_id}): {e}")

        except Exception as e:
            session.rollback()
            logger.error(f"Haydovchi {driver.id} uchun xatolik yuz berdi: {e}")

# =============================================================================
# APScheduler versiyasi (tavsiya etiladi)
# =============================================================================
def start_scheduler(bot: Bot, interval_hours: int = 24):
    """
    APScheduler yordamida check_expired_subscriptions funksiyasini
    berilgan intervalda ishga tushuradi.

    :param bot: telegram.Bot obyekti
    :param interval_hours: necha soatda bir marta tekshirilsin (default: 24 soat)
    :return: AsyncIOScheduler obyekti
    """
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
    except ImportError:
        logger.error(
            "APScheduler o'rnatilmagan! "
            "Buning uchun 'pip install apscheduler' buyrug'ini bajaring."
        )
        return None

    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        check_expired_subscriptions,
        "interval",
        hours=interval_hours,
        args=[bot],
        id="check_expired_subscriptions",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Obuna muddati tekshiruvi boshlandi: har {interval_hours} soatda bir marta."
    )
    return scheduler


# =============================================================================
# asyncio versiyasi (APScheduler o'rnatilmasa ishlatilishi mumkin)
# =============================================================================
async def run_periodic_check(bot: Bot, interval_seconds: int = 86400):
    """
    asyncio tsiklida check_expired_subscriptions ni doimiy ravishda ishga tushiradi.

    :param bot: telegram.Bot obyekti
    :param interval_seconds: tekshiruv oralig'i soniyada (default: 86400 = 24 soat)
    """
    while True:
        try:
            await check_expired_subscriptions(bot)
        except Exception as e:
            logger.error(f"Periodik tekshiruvda xatolik: {e}")
        await asyncio.sleep(interval_seconds)