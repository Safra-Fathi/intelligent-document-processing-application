"""add full name to users

Revision ID: f846d570207c
Revises: 367114320f3d
Create Date: 2026-09-23 10:21:44.963949

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f846d570207c"
down_revision: Union[str, Sequence[str], None] = "367114320f3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add full_name to users."""

    # Add as nullable first because existing users already
    # exist in the database.
    op.add_column(
        "users",
        sa.Column(
            "full_name",
            sa.String(length=100),
            nullable=True,
        ),
    )

    # Give existing users a temporary display name using
    # the part of their email before the @ symbol.
    op.execute(
        """
        UPDATE users
        SET full_name = split_part(email, '@', 1)
        WHERE full_name IS NULL
        """
    )

    # All existing rows now contain a value, so the column
    # can safely become required.
    op.alter_column(
        "users",
        "full_name",
        existing_type=sa.String(length=100),
        nullable=False,
    )


def downgrade() -> None:
    """Remove full_name from users."""

    op.drop_column(
        "users",
        "full_name",
    )