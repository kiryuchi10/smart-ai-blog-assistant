"""Create publishing and analytics automation schema

Revision ID: 002
Revises: 001
Create Date: 2025-01-28 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create blog_posts table (enhanced from existing)
    op.create_table('blog_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_description', sa.String(length=160), nullable=True),
        sa.Column('keywords', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='draft'),
        sa.Column('post_type', sa.String(length=50), nullable=False, default='article'),
        sa.Column('content_source', sa.String(length=50), nullable=False, default='manual'),
        sa.Column('tone', sa.String(length=50), nullable=False, default='professional'),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('seo_score', sa.Integer(), nullable=False, default=0),
        sa.Column('word_count', sa.Integer(), nullable=False, default=0),
        sa.Column('reading_time', sa.Integer(), nullable=False, default=0),
        sa.Column('folder_path', sa.String(length=500), nullable=True),
        sa.Column('api_data_sources', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('enhancement_applied', sa.Boolean(), nullable=False, default=False),
        sa.Column('slug', sa.String(length=500), nullable=True),
        sa.Column('featured_image_url', sa.String(length=500), nullable=True),
        sa.Column('is_template', sa.Boolean(), nullable=False, default=False),
        sa.Column('template_category', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    op.create_index(op.f('ix_blog_posts_id'), 'blog_posts', ['id'], unique=False)
    op.create_index(op.f('ix_blog_posts_user_id'), 'blog_posts', ['user_id'], unique=False)
    op.create_index(op.f('ix_blog_posts_status'), 'blog_posts', ['status'], unique=False)

    # Create content_templates table
    op.create_table('content_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_content', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('template_type', sa.String(length=50), nullable=False, default='article'),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('tone', sa.String(length=50), nullable=False, default='professional'),
        sa.Column('is_public', sa.Boolean(), nullable=False, default=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('performance_score', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('data_requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('chart_templates', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('seo_guidelines', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('placeholders', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_templates_id'), 'content_templates', ['id'], unique=False)

    # Create folder_processing_logs table
    op.create_table('folder_processing_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('folder_path', sa.String(length=500), nullable=False),
        sa.Column('folder_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('total_files', sa.Integer(), nullable=False, default=0),
        sa.Column('processed_files', sa.Integer(), nullable=False, default=0),
        sa.Column('content_files', sa.Integer(), nullable=False, default=0),
        sa.Column('image_files', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extracted_title', sa.String(length=500), nullable=True),
        sa.Column('extracted_content_length', sa.Integer(), nullable=False, default=0),
        sa.Column('extracted_images', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extracted_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('auto_publish_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('target_platforms', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_folder_processing_logs_id'), 'folder_processing_logs', ['id'], unique=False)
    op.create_index(op.f('ix_folder_processing_logs_user_id'), 'folder_processing_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_folder_processing_logs_status'), 'folder_processing_logs', ['status'], unique=False)

    # Create scheduled_posts table
    op.create_table('scheduled_posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=100), nullable=False, default='UTC'),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('platform_post_id', sa.String(length=255), nullable=True),
        sa.Column('platform_url', sa.String(length=500), nullable=True),
        sa.Column('custom_formatting', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('auto_generated', sa.Boolean(), nullable=False, default=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_posts_id'), 'scheduled_posts', ['id'], unique=False)
    op.create_index(op.f('ix_scheduled_posts_platform'), 'scheduled_posts', ['platform'], unique=False)
    op.create_index(op.f('ix_scheduled_posts_status'), 'scheduled_posts', ['status'], unique=False)
    op.create_index(op.f('ix_scheduled_posts_scheduled_time'), 'scheduled_posts', ['scheduled_time'], unique=False)

    # Create publishing_results table
    op.create_table('publishing_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('platform_post_id', sa.String(length=255), nullable=True),
        sa.Column('platform_url', sa.String(length=500), nullable=True),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('views', sa.Integer(), nullable=False, default=0),
        sa.Column('likes', sa.Integer(), nullable=False, default=0),
        sa.Column('shares', sa.Integer(), nullable=False, default=0),
        sa.Column('comments', sa.Integer(), nullable=False, default=0),
        sa.Column('click_through_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.Column('engagement_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_publishing_results_id'), 'publishing_results', ['id'], unique=False)
    op.create_index(op.f('ix_publishing_results_platform'), 'publishing_results', ['platform'], unique=False)
    op.create_index(op.f('ix_publishing_results_status'), 'publishing_results', ['status'], unique=False)

    # Create platform_integrations table
    op.create_table('platform_integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('platform_user_id', sa.String(length=255), nullable=True),
        sa.Column('platform_username', sa.String(length=255), nullable=True),
        sa.Column('custom_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('auto_publish_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('default_tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('default_category', sa.String(length=100), nullable=True),
        sa.Column('content_format_preferences', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_platform_integrations_id'), 'platform_integrations', ['id'], unique=False)
    op.create_index(op.f('ix_platform_integrations_platform'), 'platform_integrations', ['platform'], unique=False)

    # Create post_analytics table
    op.create_table('post_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=True),
        sa.Column('views', sa.Integer(), nullable=False, default=0),
        sa.Column('unique_views', sa.Integer(), nullable=False, default=0),
        sa.Column('likes', sa.Integer(), nullable=False, default=0),
        sa.Column('shares', sa.Integer(), nullable=False, default=0),
        sa.Column('comments', sa.Integer(), nullable=False, default=0),
        sa.Column('click_through_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.Column('engagement_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.Column('bounce_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.Column('time_on_page', sa.Integer(), nullable=False, default=0),
        sa.Column('conversion_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('search_impressions', sa.Integer(), nullable=False, default=0),
        sa.Column('search_clicks', sa.Integer(), nullable=False, default=0),
        sa.Column('average_position', sa.Numeric(precision=5, scale=2), nullable=False, default=0),
        sa.Column('retweets', sa.Integer(), nullable=False, default=0),
        sa.Column('mentions', sa.Integer(), nullable=False, default=0),
        sa.Column('saves', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_post_analytics_id'), 'post_analytics', ['id'], unique=False)
    op.create_index(op.f('ix_post_analytics_platform'), 'post_analytics', ['platform'], unique=False)

    # Create comment_analysis table
    op.create_table('comment_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform', sa.String(length=100), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('comment_author', sa.String(length=255), nullable=True),
        sa.Column('comment_id', sa.String(length=255), nullable=True),
        sa.Column('sentiment_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('sentiment_label', sa.String(length=50), nullable=True),
        sa.Column('extracted_questions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('extracted_complaints', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('extracted_suggestions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('comment_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('emotion_detected', sa.String(length=50), nullable=True),
        sa.Column('topics_mentioned', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_spam', sa.Boolean(), nullable=False, default=False),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comment_analysis_id'), 'comment_analysis', ['id'], unique=False)
    op.create_index(op.f('ix_comment_analysis_platform'), 'comment_analysis', ['platform'], unique=False)
    op.create_index(op.f('ix_comment_analysis_sentiment_label'), 'comment_analysis', ['sentiment_label'], unique=False)

    # Create content_recommendations table
    op.create_table('content_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recommendation_type', sa.String(length=100), nullable=False),
        sa.Column('recommendation_text', sa.Text(), nullable=False),
        sa.Column('priority_score', sa.Integer(), nullable=False, default=0),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_impact', sa.String(length=50), nullable=True),
        sa.Column('implementation_difficulty', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_content_recommendations_id'), 'content_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_content_recommendations_recommendation_type'), 'content_recommendations', ['recommendation_type'], unique=False)
    op.create_index(op.f('ix_content_recommendations_priority_score'), 'content_recommendations', ['priority_score'], unique=False)
    op.create_index(op.f('ix_content_recommendations_status'), 'content_recommendations', ['status'], unique=False)

    # Create performance_summaries table
    op.create_table('performance_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_views', sa.Integer(), nullable=False, default=0),
        sa.Column('total_engagement', sa.Integer(), nullable=False, default=0),
        sa.Column('best_performing_platform', sa.String(length=100), nullable=True),
        sa.Column('overall_sentiment_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('seo_performance_score', sa.Integer(), nullable=False, default=0),
        sa.Column('recommendation_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_likes', sa.Integer(), nullable=False, default=0),
        sa.Column('total_shares', sa.Integer(), nullable=False, default=0),
        sa.Column('total_comments', sa.Integer(), nullable=False, default=0),
        sa.Column('average_engagement_rate', sa.Numeric(precision=5, scale=4), nullable=False, default=0),
        sa.Column('views_trend', sa.String(length=20), nullable=True),
        sa.Column('engagement_trend', sa.String(length=20), nullable=True),
        sa.Column('sentiment_trend', sa.String(length=20), nullable=True),
        sa.Column('readability_score', sa.Integer(), nullable=False, default=0),
        sa.Column('seo_optimization_score', sa.Integer(), nullable=False, default=0),
        sa.Column('content_uniqueness_score', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id')
    )
    op.create_index(op.f('ix_performance_summaries_id'), 'performance_summaries', ['id'], unique=False)

    # Create api_data_requests table
    op.create_table('api_data_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('api_source', sa.String(length=100), nullable=False),
        sa.Column('request_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('charts_generated', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('request_type', sa.String(length=100), nullable=True),
        sa.Column('data_points_retrieved', sa.Integer(), nullable=False, default=0),
        sa.Column('processing_time_ms', sa.Integer(), nullable=False, default=0),
        sa.Column('cost_credits', sa.Numeric(precision=10, scale=4), nullable=False, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['post_id'], ['blog_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_data_requests_id'), 'api_data_requests', ['id'], unique=False)
    op.create_index(op.f('ix_api_data_requests_api_source'), 'api_data_requests', ['api_source'], unique=False)
    op.create_index(op.f('ix_api_data_requests_status'), 'api_data_requests', ['status'], unique=False)

    # Create folder_watcher_status table
    op.create_table('folder_watcher_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False, default='folder_watcher'),
        sa.Column('is_running', sa.Boolean(), nullable=False, default=False),
        sa.Column('monitored_path', sa.String(length=500), nullable=False),
        sa.Column('published_path', sa.String(length=500), nullable=False),
        sa.Column('failed_path', sa.String(length=500), nullable=False),
        sa.Column('total_folders_processed', sa.Integer(), nullable=False, default=0),
        sa.Column('successful_processes', sa.Integer(), nullable=False, default=0),
        sa.Column('failed_processes', sa.Integer(), nullable=False, default=0),
        sa.Column('currently_processing', sa.Integer(), nullable=False, default=0),
        sa.Column('average_processing_time', sa.Integer(), nullable=False, default=0),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_publish_enabled', sa.Boolean(), nullable=False, default=False),
        sa.Column('max_concurrent_processes', sa.Integer(), nullable=False, default=5),
        sa.Column('last_health_check', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('health_status', sa.String(length=50), nullable=False, default='healthy'),
        sa.Column('health_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_folder_watcher_status_id'), 'folder_watcher_status', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_folder_watcher_status_id'), table_name='folder_watcher_status')
    op.drop_table('folder_watcher_status')
    op.drop_index(op.f('ix_api_data_requests_status'), table_name='api_data_requests')
    op.drop_index(op.f('ix_api_data_requests_api_source'), table_name='api_data_requests')
    op.drop_index(op.f('ix_api_data_requests_id'), table_name='api_data_requests')
    op.drop_table('api_data_requests')
    op.drop_index(op.f('ix_performance_summaries_id'), table_name='performance_summaries')
    op.drop_table('performance_summaries')
    op.drop_index(op.f('ix_content_recommendations_status'), table_name='content_recommendations')
    op.drop_index(op.f('ix_content_recommendations_priority_score'), table_name='content_recommendations')
    op.drop_index(op.f('ix_content_recommendations_recommendation_type'), table_name='content_recommendations')
    op.drop_index(op.f('ix_content_recommendations_id'), table_name='content_recommendations')
    op.drop_table('content_recommendations')
    op.drop_index(op.f('ix_comment_analysis_sentiment_label'), table_name='comment_analysis')
    op.drop_index(op.f('ix_comment_analysis_platform'), table_name='comment_analysis')
    op.drop_index(op.f('ix_comment_analysis_id'), table_name='comment_analysis')
    op.drop_table('comment_analysis')
    op.drop_index(op.f('ix_post_analytics_platform'), table_name='post_analytics')
    op.drop_index(op.f('ix_post_analytics_id'), table_name='post_analytics')
    op.drop_table('post_analytics')
    op.drop_index(op.f('ix_platform_integrations_platform'), table_name='platform_integrations')
    op.drop_index(op.f('ix_platform_integrations_id'), table_name='platform_integrations')
    op.drop_table('platform_integrations')
    op.drop_index(op.f('ix_publishing_results_status'), table_name='publishing_results')
    op.drop_index(op.f('ix_publishing_results_platform'), table_name='publishing_results')
    op.drop_index(op.f('ix_publishing_results_id'), table_name='publishing_results')
    op.drop_table('publishing_results')
    op.drop_index(op.f('ix_scheduled_posts_scheduled_time'), table_name='scheduled_posts')
    op.drop_index(op.f('ix_scheduled_posts_status'), table_name='scheduled_posts')
    op.drop_index(op.f('ix_scheduled_posts_platform'), table_name='scheduled_posts')
    op.drop_index(op.f('ix_scheduled_posts_id'), table_name='scheduled_posts')
    op.drop_table('scheduled_posts')
    op.drop_index(op.f('ix_folder_processing_logs_status'), table_name='folder_processing_logs')
    op.drop_index(op.f('ix_folder_processing_logs_user_id'), table_name='folder_processing_logs')
    op.drop_index(op.f('ix_folder_processing_logs_id'), table_name='folder_processing_logs')
    op.drop_table('folder_processing_logs')
    op.drop_index(op.f('ix_content_templates_id'), table_name='content_templates')
    op.drop_table('content_templates')
    op.drop_index(op.f('ix_blog_posts_status'), table_name='blog_posts')
    op.drop_index(op.f('ix_blog_posts_user_id'), table_name='blog_posts')
    op.drop_index(op.f('ix_blog_posts_id'), table_name='blog_posts')
    op.drop_table('blog_posts')