"""Initial schema (users, applications, status_history)

This is the schema of the first prototype. A database created before Alembic
was added already has these tables: run `alembic stamp 0001` on it, then
`alembic upgrade head`.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("position", sa.String(200), nullable=False),
        sa.Column("job_url", sa.String(500)),
        sa.Column("location", sa.String(200)),
        sa.Column("source", sa.String(100)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("deadline", sa.Date()),
        sa.Column("interview_date", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_applications_id", "applications", ["id"])

    op.create_table(
        "status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id"), nullable=False),
        sa.Column("old_status", sa.String(20)),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_status_history_id", "status_history", ["id"])


def downgrade() -> None:
    op.drop_table("status_history")
    op.drop_table("applications")
    op.drop_table("users")
