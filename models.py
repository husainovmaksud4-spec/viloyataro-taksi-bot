from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Driver(Base):
    """
    Haydovchilar (Drivers) jadvali.

    Yangi maydonlar — oylik obuna (to'lov) tizimi uchun:
      - payment_status: to'lov holati ('unpaid', 'pending', 'paid')
      - subscription_ends_at: obuna tugash sanasi (nullable)
      - is_verified: admin tomonidan tasdiqlanganmi?
      - telegram_id: haydovchining Telegram ID si
    """

    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(
        BigInteger,
        unique=True,
        nullable=True,
        comment="Haydovchining Telegram ID si",
    )

    # Mavjud maydonlar (masalan) — ishchi loyihaga moslashtiring:
    # full_name = Column(String(100), nullable=False)
    # phone = Column(String(20), unique=True, nullable=False)
    # car_number = Column(String(20))
    # created_at = Column(DateTime, default=datetime.utcnow)

    # =========================================================================
    # YANGI: oylik obuna to'lov maydonlari
    # =========================================================================
    payment_status = Column(
        String(20),
        nullable=False,
        default="unpaid",
        server_default="unpaid",
        comment="To'lov holati: 'unpaid' (to'lanmagan), 'pending' (kutilmoqda), 'paid' (to'langan)",
    )
    subscription_ends_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Obuna tugash sanasi; to'lov tasdiqlangach hozirgi vaqt + 30 kun yoziladi",
    )

    # YANGI: admin tomonidan tasdiqlanganmi
    is_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        comment="Admin to'lovingizni tasdiqlaganmi?",
    )

    __table_args__ = (
        CheckConstraint(
            payment_status.in_(["unpaid", "pending", "paid"]),
            name="ck_drivers_payment_status",
        ),
    )

    # -------------------------------------------------------------------------
    # YANGI: to'lovni tasdiqlab obunani faollashtirish
    # -------------------------------------------------------------------------
    def confirm_payment(self):
        """
        To'lovni 'paid' deb belgilaydi, is_verified=True qiladi va
        subscription_ends_at ni hozirgi vaqtga SUBSCRIPTION_DAYS (30) kun
        qo'shish orqali o'rnaydi.
        """
        self.payment_status = "paid"
        self.is_verified = True
        self.subscription_ends_at = datetime.now(timezone.utc) + timedelta(
            days=30
        )
        return self

    def is_subscription_active(self):
        """Obuna hali amal qiladi-mi? (payment_status='paid' va muddat o'tmagan bo'lsa True)"""
        if self.payment_status != "paid" or self.subscription_ends_at is None:
            return False
        return datetime.now(timezone.utc) < self.subscription_ends_at

    def __repr__(self):
        return (
            f"<Driver(id={self.id}, telegram_id={self.telegram_id}, "
            f"payment_status={self.payment_status}, is_verified={self.is_verified}, "
            f"subscription_ends_at={self.subscription_ends_at})>"
        )