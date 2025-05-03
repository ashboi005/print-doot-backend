"""remove user_customization_options field

Revision ID: 6dd62ae35721
Revises: 8d3e61c9e773
Create Date: 2025-05-03 16:44:11.617929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dd62ae35721'
down_revision: Union[str, None] = '8d3e61c9e773'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
