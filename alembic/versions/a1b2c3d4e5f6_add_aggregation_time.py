"""add aggregation_time to time_profiling

Revision ID: a1b2c3d4e5f6
Revises: f917d9d152b9
Create Date: 2026-01-11 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f917d9d152b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add aggregation_time column to time_profiling table
    op.add_column('time_profiling',
        sa.Column('aggregation_time', sa.Float(), nullable=False, server_default='0.0')
    )


def downgrade() -> None:
    # Remove aggregation_time column from time_profiling table
    op.drop_column('time_profiling', 'aggregation_time')
