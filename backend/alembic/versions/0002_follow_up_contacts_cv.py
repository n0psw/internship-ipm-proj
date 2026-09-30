"""Follow-up date, contact, CV version; indexes on foreign keys

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("applications") as batch:
        batch.add_column(sa.Column("follow_up_date", sa.Date()))
        batch.add_column(sa.Column("contact_name", sa.String(200)))
        batch.add_column(sa.Column("contact_info", sa.String(300)))
        batch.add_column(sa.Column("cv_version", sa.String(200)))
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_status_history_application_id", "status_history", ["application_id"])


def downgrade() -> None:
    op.drop_index("ix_status_history_application_id", table_name="status_history")
    op.drop_index("ix_applications_user_id", table_name="applications")
    with op.batch_alter_table("applications") as batch:
        batch.drop_column("cv_version")
        batch.drop_column("contact_info")
        batch.drop_column("contact_name")
        batch.drop_column("follow_up_date")
