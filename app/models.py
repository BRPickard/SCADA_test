from datetime import datetime
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="Viewer")


class SourceSystem(Base):
    __tablename__ = "source_systems"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    connector_type: Mapped[str] = mapped_column(String(64))
    endpoint: Mapped[str] = mapped_column(String(255), default="")
    auth_json: Mapped[dict] = mapped_column(JSON, default=dict)
    cadence_minutes: Mapped[int] = mapped_column(Integer, default=60)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SourceMapping(Base):
    __tablename__ = "source_mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_system_id: Mapped[int] = mapped_column(ForeignKey("source_systems.id"))
    entity_name: Mapped[str] = mapped_column(String(64))
    source_field: Mapped[str] = mapped_column(String(128))
    target_field: Mapped[str] = mapped_column(String(128))


class SyncRun(Base):
    __tablename__ = "sync_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_system_id: Mapped[int] = mapped_column(ForeignKey("source_systems.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running")
    record_count: Mapped[int] = mapped_column(Integer, default=0)
    error_text: Mapped[str] = mapped_column(Text, default="")


class Site(Base):
    __tablename__ = "sites"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(64), default="unknown")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    owner: Mapped[str] = mapped_column(String(255), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    source_system_id: Mapped[int | None] = mapped_column(ForeignKey("source_systems.id"), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Asset(Base):
    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("source_system_id", "source_record_id", name="uq_asset_source_record"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(128), default="")
    make: Mapped[str] = mapped_column(String(128), default="")
    model: Mapped[str] = mapped_column(String(128), default="")
    serial: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(64), default="active")
    condition_score: Mapped[float] = mapped_column(Float, default=50)
    protocols: Mapped[str] = mapped_column(Text, default="")
    network_notes: Mapped[str] = mapped_column(Text, default="")
    cyber_notes: Mapped[str] = mapped_column(Text, default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_system_id: Mapped[int | None] = mapped_column(ForeignKey("source_systems.id"), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    risk_override: Mapped[float | None] = mapped_column(Float, nullable=True)


class AssetAttachment(Base):
    __tablename__ = "asset_attachments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    attachment_name: Mapped[str] = mapped_column(String(255))
    attachment_url_or_id: Mapped[str] = mapped_column(String(500))
    source_system_id: Mapped[int | None] = mapped_column(ForeignKey("source_systems.id"), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(64), default="")
    start_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    total_cost: Mapped[float] = mapped_column(Float, default=0)
    cost_capex: Mapped[float] = mapped_column(Float, default=0)
    cost_opex: Mapped[float] = mapped_column(Float, default=0)
    resource_internal_fte: Mapped[float] = mapped_column(Float, default=0)
    resource_external_fte: Mapped[float] = mapped_column(Float, default=0)
    dependencies: Mapped[str] = mapped_column(Text, default="")
    risk_likelihood: Mapped[float] = mapped_column(Float, default=1)
    risk_impact: Mapped[float] = mapped_column(Float, default=1)
    source_system_id: Mapped[int | None] = mapped_column(ForeignKey("source_systems.id"), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fiscal_year: Mapped[int] = mapped_column(Integer)
    budget_bucket: Mapped[str] = mapped_column(String(64))
    available_amount: Mapped[float] = mapped_column(Float, default=0)
    committed_amount: Mapped[float] = mapped_column(Float, default=0)
    source_system_id: Mapped[int | None] = mapped_column(ForeignKey("source_systems.id"), nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    settings_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(64), default="system")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
