"""Add investment and finance tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create investment_profiles table
    op.create_table('investment_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_tolerance', sa.String(length=20), nullable=True),
        sa.Column('investment_goals', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('preferred_sectors', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('watchlist_symbols', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('trading_style', sa.String(length=50), nullable=True),
        sa.Column('portfolio_value', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('monthly_investment_budget', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('experience_level', sa.String(length=20), nullable=True),
        sa.Column('notification_preferences', sa.JSON(), nullable=True),
        sa.Column('analysis_preferences', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_investment_profiles_id'), 'investment_profiles', ['id'], unique=False)

    # Create investment_transactions table
    op.create_table('investment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('quantity', sa.DECIMAL(precision=15, scale=6), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fees', sa.DECIMAL(precision=10, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sentiment_at_time', sa.JSON(), nullable=True),
        sa.CheckConstraint("transaction_type IN ('buy', 'sell', 'dividend', 'split')", name='check_transaction_type'),
        sa.ForeignKeyConstraint(['profile_id'], ['investment_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_transaction_symbol', 'investment_transactions', ['symbol'], unique=False)
    op.create_index('idx_transaction_date', 'investment_transactions', ['transaction_date'], unique=False)
    op.create_index(op.f('ix_investment_transactions_id'), 'investment_transactions', ['id'], unique=False)

    # Create portfolio_holdings table
    op.create_table('portfolio_holdings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('current_quantity', sa.DECIMAL(precision=15, scale=6), nullable=True),
        sa.Column('average_cost', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('total_invested', sa.DECIMAL(precision=15, scale=2), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['profile_id'], ['investment_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_holding_symbol', 'portfolio_holdings', ['symbol'], unique=False)
    op.create_index(op.f('ix_portfolio_holdings_id'), 'portfolio_holdings', ['id'], unique=False)

    # Create market_data table
    op.create_table('market_data',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open_price', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('high_price', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('low_price', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('close_price', sa.DECIMAL(precision=10, scale=4), nullable=False),
        sa.Column('volume', sa.Integer(), nullable=True),
        sa.Column('adjusted_close', sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column('data_source', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_market_data_symbol', 'market_data', ['symbol'], unique=False)
    op.create_index('idx_market_data_timestamp', 'market_data', ['timestamp'], unique=False)
    op.create_index(op.f('ix_market_data_id'), 'market_data', ['id'], unique=False)

    # Create sentiment_analysis table
    op.create_table('sentiment_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('sentiment_score', sa.DECIMAL(precision=5, scale=4), nullable=False),
        sa.Column('confidence', sa.DECIMAL(precision=5, scale=4), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('entities_mentioned', postgresql.ARRAY(sa.String()), nullable=True),
        sa.CheckConstraint("content_type IN ('news', 'social', 'community')", name='check_content_type'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sentiment_symbol', 'sentiment_analysis', ['symbol'], unique=False)
    op.create_index('idx_sentiment_timestamp', 'sentiment_analysis', ['timestamp'], unique=False)
    op.create_index(op.f('ix_sentiment_analysis_id'), 'sentiment_analysis', ['id'], unique=False)

    # Create investment_alerts table
    op.create_table('investment_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('alert_type', sa.String(length=20), nullable=False),
        sa.Column('condition_type', sa.String(length=20), nullable=False),
        sa.Column('threshold_value', sa.DECIMAL(precision=15, scale=4), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_triggered', sa.Boolean(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.CheckConstraint("alert_type IN ('price', 'sentiment', 'volume', 'news')", name='check_alert_type'),
        sa.CheckConstraint("condition_type IN ('above', 'below', 'change_percent')", name='check_condition_type'),
        sa.ForeignKeyConstraint(['profile_id'], ['investment_profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_investment_alerts_id'), 'investment_alerts', ['id'], unique=False)

    # Create investment_insights table
    op.create_table('investment_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('insight_type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence_level', sa.String(length=10), nullable=False),
        sa.Column('supporting_data', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.CheckConstraint("insight_type IN ('recommendation', 'analysis', 'alert', 'trend')", name='check_insight_type'),
        sa.CheckConstraint("confidence_level IN ('low', 'medium', 'high')", name='check_confidence_level'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_insight_symbol', 'investment_insights', ['symbol'], unique=False)
    op.create_index('idx_insight_timestamp', 'investment_insights', ['timestamp'], unique=False)
    op.create_index(op.f('ix_investment_insights_id'), 'investment_insights', ['id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_investment_insights_id'), table_name='investment_insights')
    op.drop_index('idx_insight_timestamp', table_name='investment_insights')
    op.drop_index('idx_insight_symbol', table_name='investment_insights')
    op.drop_table('investment_insights')
    
    op.drop_index(op.f('ix_investment_alerts_id'), table_name='investment_alerts')
    op.drop_table('investment_alerts')
    
    op.drop_index(op.f('ix_sentiment_analysis_id'), table_name='sentiment_analysis')
    op.drop_index('idx_sentiment_timestamp', table_name='sentiment_analysis')
    op.drop_index('idx_sentiment_symbol', table_name='sentiment_analysis')
    op.drop_table('sentiment_analysis')
    
    op.drop_index(op.f('ix_market_data_id'), table_name='market_data')
    op.drop_index('idx_market_data_timestamp', table_name='market_data')
    op.drop_index('idx_market_data_symbol', table_name='market_data')
    op.drop_table('market_data')
    
    op.drop_index(op.f('ix_portfolio_holdings_id'), table_name='portfolio_holdings')
    op.drop_index('idx_holding_symbol', table_name='portfolio_holdings')
    op.drop_table('portfolio_holdings')
    
    op.drop_index(op.f('ix_investment_transactions_id'), table_name='investment_transactions')
    op.drop_index('idx_transaction_date', table_name='investment_transactions')
    op.drop_index('idx_transaction_symbol', table_name='investment_transactions')
    op.drop_table('investment_transactions')
    
    op.drop_index(op.f('ix_investment_profiles_id'), table_name='investment_profiles')
    op.drop_table('investment_profiles')