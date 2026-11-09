"""add password hashes for local JWT authentication

Revision ID: 0003_local_jwt_auth
Revises: 0002_workspace_resources
"""
from alembic import op

revision = "0003_local_jwt_auth"
down_revision = "0002_workspace_resources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash varchar(256)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email))")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_email_lower")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS password_hash")
