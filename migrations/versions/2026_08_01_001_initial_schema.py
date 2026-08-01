"""Initial schema creation - All core tables.

Revision ID: 001
Revises: 
Create Date: 2026-08-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.database.database import GUID, JSONType

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('employee_id', sa.String(20), nullable=False),
        sa.Column('username', sa.String(80), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('department', sa.String(100), nullable=False),
        sa.Column('designation', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('language', sa.String(5), nullable=False),
        sa.Column('timezone', sa.String(60), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_employees_email'), 'employees', ['email'], unique=False)
    op.create_index(op.f('ix_employees_username'), 'employees', ['username'], unique=False)
    op.create_index(op.f('ix_employees_employee_id'), 'employees', ['employee_id'], unique=False)

    # Create knowledge_base table
    op.create_table(
        'knowledge_base',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100), nullable=True),
        sa.Column('content', sa.String(10000), nullable=False),
        sa.Column('tags', JSONType(), nullable=True),
        sa.Column('source', sa.String(300), nullable=True),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('relevance_score', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_knowledge_base_category'), 'knowledge_base', ['category'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('doc_type', sa.String(80), nullable=False),
        sa.Column('department', sa.String(100), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(120), nullable=True),
        sa.Column('is_confidential', sa.Boolean(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.String(100), nullable=True),
        sa.Column('metadata', JSONType(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_documents_doc_type'), 'documents', ['doc_type'], unique=False)
    op.create_index(op.f('ix_documents_department'), 'documents', ['department'], unique=False)

    # Create actions table
    op.create_table(
        'actions',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('conversation_id', sa.String(100), nullable=True),
        sa.Column('requested_by', sa.String(200), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('natural_language', sa.String(5000), nullable=False),
        sa.Column('intent', sa.String(300), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('target_resource', sa.String(300), nullable=False),
        sa.Column('target_table', sa.String(100), nullable=True),
        sa.Column('affected_records', sa.Integer(), nullable=False),
        sa.Column('action_json', JSONType(), nullable=False),
        sa.Column('execution_plan', JSONType(), nullable=True),
        sa.Column('parameters', JSONType(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('risk_breakdown', JSONType(), nullable=True),
        sa.Column('reversibility', sa.String(30), nullable=False),
        sa.Column('data_scope', sa.String(30), nullable=False),
        sa.Column('regulatory_category', sa.String(30), nullable=False),
        sa.Column('policy_result', sa.String(20), nullable=False),
        sa.Column('policy_violations', JSONType(), nullable=True),
        sa.Column('decision', sa.String(20), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('workflow_stage', sa.String(30), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('execution_result', JSONType(), nullable=True),
        sa.Column('execution_logs', JSONType(), nullable=True),
        sa.Column('rollback_available', sa.Boolean(), nullable=False),
        sa.Column('rollback_status', sa.String(30), nullable=True),
        sa.Column('reviewed_by', sa.String(200), nullable=True),
        sa.Column('review_comment', sa.String(2000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_actions_conversation_id'), 'actions', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_actions_operation_type'), 'actions', ['operation_type'], unique=False)
    op.create_index(op.f('ix_actions_risk_level'), 'actions', ['risk_level'], unique=False)
    op.create_index(op.f('ix_actions_decision'), 'actions', ['decision'], unique=False)
    op.create_index(op.f('ix_actions_workflow_stage'), 'actions', ['workflow_stage'], unique=False)
    op.create_index(op.f('ix_actions_status'), 'actions', ['status'], unique=False)
    op.create_index(op.f('ix_actions_created_at'), 'actions', ['created_at'], unique=False)

    # Create review_queue table
    op.create_table(
        'review_queue',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('action_id', GUID(), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('action_description', sa.String(2000), nullable=False),
        sa.Column('action_json', JSONType(), nullable=False),
        sa.Column('target_resource', sa.String(300), nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('requested_by', sa.String(200), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('assigned_to', sa.String(200), nullable=True),
        sa.Column('reviewer_comment', sa.String(2000), nullable=True),
        sa.Column('reviewed_by', sa.String(200), nullable=True),
        sa.Column('reversibility', sa.String(30), nullable=False),
        sa.Column('affected_records', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('intent', sa.String(2000), nullable=True),
        sa.Column('risk_breakdown', JSONType(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_review_queue_action_id'), 'review_queue', ['action_id'], unique=False)
    op.create_index(op.f('ix_review_queue_risk_level'), 'review_queue', ['risk_level'], unique=False)
    op.create_index(op.f('ix_review_queue_priority'), 'review_queue', ['priority'], unique=False)
    op.create_index(op.f('ix_review_queue_status'), 'review_queue', ['status'], unique=False)
    op.create_index(op.f('ix_review_queue_created_at'), 'review_queue', ['created_at'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('action_id', GUID(), nullable=True),
        sa.Column('conversation_id', sa.String(100), nullable=True),
        sa.Column('event_type', sa.String(80), nullable=False),
        sa.Column('action', sa.String(200), nullable=False),
        sa.Column('operation_type', sa.String(50), nullable=True),
        sa.Column('resource', sa.String(300), nullable=False),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('actor', sa.String(200), nullable=False),
        sa.Column('actor_role', sa.String(80), nullable=True),
        sa.Column('reviewer', sa.String(200), nullable=True),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_breakdown', JSONType(), nullable=True),
        sa.Column('decision', sa.String(30), nullable=False),
        sa.Column('outcome', sa.String(30), nullable=False),
        sa.Column('rejection_reason', sa.String(1000), nullable=True),
        sa.Column('execution_status', sa.String(30), nullable=True),
        sa.Column('execution_duration_ms', sa.Float(), nullable=False),
        sa.Column('rollback_executed', sa.Boolean(), nullable=False),
        sa.Column('metadata', JSONType(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_action_id'), 'audit_logs', ['action_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_actor'), 'audit_logs', ['actor'], unique=False)
    op.create_index(op.f('ix_audit_logs_risk_level'), 'audit_logs', ['risk_level'], unique=False)
    op.create_index(op.f('ix_audit_logs_decision'), 'audit_logs', ['decision'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('key', sa.String(200), nullable=False),
        sa.Column('value', JSONType(), nullable=False),
        sa.Column('category', sa.String(80), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_secret', sa.Boolean(), nullable=False),
        sa.Column('is_editable', sa.Boolean(), nullable=False),
        sa.Column('updated_by', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=False)
    op.create_index(op.f('ix_settings_category'), 'settings', ['category'], unique=False)


def downgrade() -> None:
    op.drop_table('settings')
    op.drop_table('audit_logs')
    op.drop_table('review_queue')
    op.drop_table('actions')
    op.drop_table('documents')
    op.drop_table('knowledge_base')
    op.drop_table('employees')
