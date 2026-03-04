"""initial

Revision ID: 0001
Revises: 
Create Date: 2026-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('users', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('username', sa.String(64), unique=True), sa.Column('password_hash', sa.String(255)), sa.Column('role', sa.String(32)))
    op.create_table('source_systems', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(120), unique=True), sa.Column('connector_type', sa.String(64)), sa.Column('endpoint', sa.String(255)), sa.Column('auth_json', sa.JSON()), sa.Column('cadence_minutes', sa.Integer()), sa.Column('enabled', sa.Boolean()), sa.Column('created_at', sa.DateTime()))
    op.create_table('sync_runs', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('source_system_id', sa.Integer()), sa.Column('started_at', sa.DateTime()), sa.Column('finished_at', sa.DateTime(), nullable=True), sa.Column('status', sa.String(32)), sa.Column('record_count', sa.Integer()), sa.Column('error_text', sa.Text()))
    op.create_table('sites', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255)), sa.Column('type', sa.String(64)), sa.Column('lat', sa.Float(), nullable=True), sa.Column('lon', sa.Float(), nullable=True), sa.Column('owner', sa.String(255)), sa.Column('notes', sa.Text()), sa.Column('source_system_id', sa.Integer(), nullable=True), sa.Column('source_record_id', sa.String(128), nullable=True), sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    op.create_table('assets', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('site_id', sa.Integer(), nullable=True), sa.Column('asset_type', sa.String(128)), sa.Column('make', sa.String(128)), sa.Column('model', sa.String(128)), sa.Column('serial', sa.String(128)), sa.Column('status', sa.String(64)), sa.Column('condition_score', sa.Float()), sa.Column('protocols', sa.Text()), sa.Column('network_notes', sa.Text()), sa.Column('cyber_notes', sa.Text()), sa.Column('lat', sa.Float(), nullable=True), sa.Column('lon', sa.Float(), nullable=True), sa.Column('source_system_id', sa.Integer(), nullable=True), sa.Column('source_record_id', sa.String(128), nullable=True), sa.Column('last_synced_at', sa.DateTime(), nullable=True), sa.Column('risk_override', sa.Float(), nullable=True))
    op.create_table('projects', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255)), sa.Column('description', sa.Text()), sa.Column('category', sa.String(64)), sa.Column('start_date', sa.Date(), nullable=True), sa.Column('end_date', sa.Date(), nullable=True), sa.Column('total_cost', sa.Float()), sa.Column('cost_capex', sa.Float()), sa.Column('cost_opex', sa.Float()), sa.Column('resource_internal_fte', sa.Float()), sa.Column('resource_external_fte', sa.Float()), sa.Column('dependencies', sa.Text()), sa.Column('risk_likelihood', sa.Float()), sa.Column('risk_impact', sa.Float()), sa.Column('source_system_id', sa.Integer(), nullable=True), sa.Column('source_record_id', sa.String(128), nullable=True), sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    op.create_table('budgets', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('fiscal_year', sa.Integer()), sa.Column('budget_bucket', sa.String(64)), sa.Column('available_amount', sa.Float()), sa.Column('committed_amount', sa.Float()), sa.Column('source_system_id', sa.Integer(), nullable=True), sa.Column('source_record_id', sa.String(128), nullable=True), sa.Column('last_synced_at', sa.DateTime(), nullable=True))
    op.create_table('scenarios', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(255), unique=True), sa.Column('settings_json', sa.JSON()), sa.Column('created_by', sa.String(64)), sa.Column('version', sa.Integer()), sa.Column('updated_at', sa.DateTime()))
    op.create_table('audit_log', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('actor', sa.String(64)), sa.Column('action', sa.String(255)), sa.Column('payload', sa.JSON()), sa.Column('created_at', sa.DateTime()))
    op.create_table('source_mappings', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('source_system_id', sa.Integer()), sa.Column('entity_name', sa.String(64)), sa.Column('source_field', sa.String(128)), sa.Column('target_field', sa.String(128)))


def downgrade() -> None:
    for t in ['source_mappings', 'audit_log', 'scenarios', 'budgets', 'projects', 'assets', 'sites', 'sync_runs', 'source_systems', 'users']:
        op.drop_table(t)
