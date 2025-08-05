"""Create enhanced user management and subscription schema

Revision ID: 001
Revises: 
Create Date: 2025-01-28 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create subscription_plans table
    op.create_table('subscription_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price_monthly', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_yearly', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('posts_limit', sa.Integer(), nullable=False),
        sa.Column('api_calls_limit', sa.Integer(), nullable=False),
        sa.Column('storage_limit_gb', sa.Integer(), nullable=False, default=1),
        sa.Column('folder_monitoring', sa.Boolean(), nullable=False, default=False),
        sa.Column('comment_analysis', sa.Boolean(), nullable=False, default=False),
        sa.Column('advanced_analytics', sa.Boolean(), nullable=False, default=False),
        sa.Column('priority_support', sa.Boolean(), nullable=False, default=False),
        sa.Column('multi_platform_publishing', sa.Boolean(), nullable=False, default=False),
        sa.Column('ai_content_enhancement', sa.Boolean(), nullable=False, default=False),
        sa.Column('api_data_integration', sa.Boolean(), nullable=False, default=False),
        sa.Column('custom_templates', sa.Boolean(), nullable=False, default=False),
        sa.Column('bulk_operations', sa.Boolean(), nullable=False, default=False),
        sa.Column('white_label', sa.Boolean(), nullable=False, default=False),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=False, default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_popular', sa.Boolean(), nullable=False, default=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, default=0),
        sa.Column('trial_days', sa.Integer(), nullable=False, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_subscription_plans_id'), 'subscription_plans', ['id'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('subscription_tier', sa.String(length=50), nullable=False, default='free'),
        sa.Column('subscription_status', sa.String(length=50), nullable=False, default='active'),
        sa.Column('subscription_plan_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('posts_used_this_month', sa.Integer(), nullable=False, default=0),
        sa.Column('posts_limit', sa.Integer(), nullable=False, default=5),
        sa.Column('api_calls_used_this_month', sa.Integer(), nullable=False, default=0),
        sa.Column('api_calls_limit', sa.Integer(), nullable=False, default=100),
        sa.Column('folder_monitoring_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('comment_analysis_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('advanced_analytics_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('priority_support_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('preferred_platforms', postgresql.ARRAY(sa.String()), nullable=False, default='{}'),
        sa.Column('default_content_tone', sa.String(length=50), nullable=False, default='professional'),
        sa.Column('default_content_length', sa.String(length=20), nullable=False, default='medium'),
        sa.Column('timezone', sa.String(length=100), nullable=False, default='UTC'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('subscription_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('subscription_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usage_reset_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['subscription_plan_id'], ['subscription_plans.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('stripe_customer_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Insert default subscription plans
    op.execute("""
        INSERT INTO subscription_plans (
            id, name, description, price_monthly, posts_limit, api_calls_limit, 
            storage_limit_gb, folder_monitoring, comment_analysis, advanced_analytics,
            priority_support, multi_platform_publishing, ai_content_enhancement,
            api_data_integration, custom_templates, bulk_operations, white_label,
            trial_days, is_active, sort_order
        ) VALUES 
        (
            gen_random_uuid(), 'Free', 'Perfect for getting started with basic blog automation',
            0, 5, 100, 1, false, false, false, false, false, true, false, false, false, false,
            0, true, 1
        ),
        (
            gen_random_uuid(), 'Starter', 'Ideal for individual bloggers and content creators',
            19.99, 50, 1000, 10, true, true, false, false, true, true, true, true, false, false,
            14, true, 2
        ),
        (
            gen_random_uuid(), 'Professional', 'Perfect for content marketers and growing businesses',
            49.99, 200, 5000, 50, true, true, true, true, true, true, true, true, true, false,
            14, true, 3
        ),
        (
            gen_random_uuid(), 'Enterprise', 'Advanced features for large teams and agencies',
            199.99, 1000, 25000, 500, true, true, true, true, true, true, true, true, true, true,
            30, true, 4
        );
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_subscription_plans_id'), table_name='subscription_plans')
    op.drop_table('subscription_plans')