"""refactor team table

Revision ID: 03c3c8f0c661
Revises: 8b6f7c2a1d4e
Create Date: 2026-03-11 22:57:28.449123
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "03c3c8f0c661"
down_revision: Union[str, Sequence[str], None] = "8b6f7c2a1d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Class-only refactor: competition.Team -> competition.TeamF1.
    # No physical database changes are required because the underlying
    # table remains competition.teams.
    pass


def downgrade() -> None:
    pass
