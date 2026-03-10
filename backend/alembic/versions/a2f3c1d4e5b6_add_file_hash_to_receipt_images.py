"""add file_hash to receipt_images

Revision ID: a2f3c1d4e5b6
Revises: 56b047f628d9
Create Date: 2026-03-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'a2f3c1d4e5b6'
down_revision = '56b047f628d9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("receipt_images")}
    if "file_hash" not in columns:
        op.add_column("receipt_images", sa.Column("file_hash", sa.String(64), nullable=True))

    indexes = {idx["name"] for idx in inspector.get_indexes("receipt_images")}
    if "ix_receipt_images_file_hash" not in indexes:
        op.create_index("ix_receipt_images_file_hash", "receipt_images", ["file_hash"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    indexes = {idx["name"] for idx in inspector.get_indexes("receipt_images")}
    if "ix_receipt_images_file_hash" in indexes:
        op.drop_index("ix_receipt_images_file_hash", table_name="receipt_images")

    columns = {col["name"] for col in inspector.get_columns("receipt_images")}
    if "file_hash" in columns:
        op.drop_column("receipt_images", "file_hash")
