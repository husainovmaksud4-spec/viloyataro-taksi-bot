"""add_driver_payment_fields

Yangilangan maydonlar:
- drivers.payment_status (String, default='unpaid')
- drivers.subscription_ends_at (DateTime, nullable)

Revision ID: add_driver_payment_fields
Revises: 
Create Date: 2026-11-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_driver_payment_fields"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "drivers",
        sa.Column(
            "payment_status",
            sa.String(length=20),
            nullable=False,
            server_default="unpaid",
        ),
    )
    op.add_column(
        "drivers",
        sa.Column("subscription_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_drivers_payment_status",
        "drivers",
        "payment_status IN ('unpaid', 'pending', 'paid')",
    )


def downgrade():
    op.drop_constraint("ck_drivers_payment_status", "drivers", type_="check")
    op.drop_column("drivers", "subscription_ends_at")
    op.drop_column("drivers", "payment_status")