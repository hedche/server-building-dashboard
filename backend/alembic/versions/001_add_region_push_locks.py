"""Add region_push_locks table

Revision ID: 001_add_region_push_locks
Revises:
Create Date: 2026-01-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_region_push_locks'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the region_push_locks table."""
    op.create_table(
        'region_push_locks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('region', sa.String(length=20), nullable=False),
        sa.Column('locked_by_email', sa.String(length=255), nullable=False),
        sa.Column('locked_by_name', sa.String(length=255), nullable=True),
        sa.Column(
            'locked_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False
        ),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('region'),
    )
    # Create index on region for faster lookups
    op.create_index(
        'ix_region_push_locks_region',
        'region_push_locks',
        ['region'],
        unique=True
    )


def downgrade() -> None:
    """Drop the region_push_locks table."""
    op.drop_index('ix_region_push_locks_region', table_name='region_push_locks')
    op.drop_table('region_push_locks')
