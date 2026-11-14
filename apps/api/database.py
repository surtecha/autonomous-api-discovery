from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Engine, Index, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class DiscoverySession(Base):
    __tablename__ = "discovery_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    target: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    strategy: Mapped[str] = mapped_column(String(16), default="gain")
    budget: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    __table_args__ = (Index("ix_sessions_status_created", "status", "created_at"),)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    category: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


def database(url: str) -> tuple[Engine, sessionmaker[Session]]:
    engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)
    return engine, sessionmaker(engine, expire_on_commit=False)
