"""complete procurement and operational HR projections

Revision ID: 0024_procurement_hr_operations
Revises: 0023_employee_birth_date
"""

from alembic import op
import sqlalchemy as sa


revision = "0024_procurement_hr_operations"
down_revision = "0023_employee_birth_date"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("employee_contracts", sa.Column("schedule_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")))
    op.add_column("attendance_entries", sa.Column("overtime_status", sa.String(length=30), nullable=False, server_default="NOT_REQUIRED"))
    op.add_column("attendance_entries", sa.Column("overtime_approved_by", sa.String(length=120), nullable=True))
    op.add_column("attendance_entries", sa.Column("overtime_approval_note", sa.String(length=500), nullable=True))
    op.create_index("ix_attendance_entries_overtime_status", "attendance_entries", ["overtime_status"], unique=False)
    op.execute("UPDATE attendance_entries SET overtime_status = 'PENDING' WHERE overtime_hours > 0")


def downgrade() -> None:
    op.drop_index("ix_attendance_entries_overtime_status", table_name="attendance_entries")
    op.drop_column("attendance_entries", "overtime_approval_note")
    op.drop_column("attendance_entries", "overtime_approved_by")
    op.drop_column("attendance_entries", "overtime_status")
    op.drop_column("employee_contracts", "schedule_json")
