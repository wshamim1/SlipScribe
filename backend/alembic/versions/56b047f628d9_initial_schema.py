"""initial schema baseline

Revision ID: 56b047f628d9
Revises:
Create Date: 2026-03-08 18:50:48.376842

"""
# revision identifiers, used by Alembic.
revision = "56b047f628d9"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Baseline migration.

    The initial schema is bootstrapped by SQL in `db/migrations/001_initial_schema.sql`
    (mounted by docker-compose into Postgres init scripts).
    """
    pass


def downgrade() -> None:
    pass
