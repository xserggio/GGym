"""add abduccion/banda enums and rde.unit

Revision ID: 136e0f211bb7
Revises: 933b368c0b14
Create Date: 2026-08-06 14:11:15.346455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.models.enums import Equipment, MovementPattern


# revision identifiers, used by Alembic.
revision: str = '136e0f211bb7'
down_revision: Union[str, Sequence[str], None] = '933b368c0b14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# New enum members (abduccion, banda) mean the exercises CHECK constraints must
# be recreated. batch_alter_table rebuilds the table with the new CHECKs.
_PATTERN = sa.Enum(*[p.value for p in MovementPattern], native_enum=False, length=32)
_EQUIPMENT = sa.Enum(*[e.value for e in Equipment], native_enum=False, length=20)
_PATTERN_OLD = sa.Enum(
    *[p.value for p in MovementPattern if p != MovementPattern.abduccion],
    native_enum=False, length=32,
)
_EQUIPMENT_OLD = sa.Enum(
    *[e.value for e in Equipment if e != Equipment.banda],
    native_enum=False, length=20,
)


def upgrade() -> None:
    with op.batch_alter_table('routine_day_exercises', schema=None) as batch_op:
        batch_op.add_column(sa.Column('unit', sa.String(length=10), server_default=sa.text("'reps'"), nullable=False))
    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.alter_column('pattern', existing_type=_PATTERN_OLD, type_=_PATTERN, existing_nullable=False)
        batch_op.alter_column('equipment', existing_type=_EQUIPMENT_OLD, type_=_EQUIPMENT, existing_nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('exercises', schema=None) as batch_op:
        batch_op.alter_column('equipment', existing_type=_EQUIPMENT, type_=_EQUIPMENT_OLD, existing_nullable=False)
        batch_op.alter_column('pattern', existing_type=_PATTERN, type_=_PATTERN_OLD, existing_nullable=False)
    with op.batch_alter_table('routine_day_exercises', schema=None) as batch_op:
        batch_op.drop_column('unit')
