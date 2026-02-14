"""add credit_report table

Revision ID: a3f7c8d2e1b4
Revises: 81211fc0af52
Create Date: 2026-02-13 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a3f7c8d2e1b4'
down_revision = '81211fc0af52'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('credit_report',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('application_id', sa.UUID(), nullable=False),
        sa.Column('credit_score', sa.Integer(), nullable=False),
        sa.Column('score_model', sa.String(length=50), nullable=False),
        sa.Column('score_factors', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tradelines', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('public_records', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('inquiries', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('collections', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('total_accounts', sa.Integer(), nullable=False),
        sa.Column('open_accounts', sa.Integer(), nullable=False),
        sa.Column('credit_utilization', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('oldest_account_months', sa.Integer(), nullable=True),
        sa.Column('avg_account_age_months', sa.Integer(), nullable=True),
        sa.Column('on_time_payments_pct', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('late_payments_30d', sa.Integer(), nullable=False),
        sa.Column('late_payments_60d', sa.Integer(), nullable=False),
        sa.Column('late_payments_90d', sa.Integer(), nullable=False),
        sa.Column('fraud_alerts', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('fraud_score', sa.Integer(), nullable=False),
        sa.Column('pulled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['application.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_credit_report_application_id', 'credit_report', ['application_id'])


def downgrade() -> None:
    op.drop_index('idx_credit_report_application_id', table_name='credit_report')
    op.drop_table('credit_report')
