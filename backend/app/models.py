from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Severity(str, Enum):
    healthy = "healthy"
    warning = "warning"
    critical = "critical"


class ApprovalState(str, Enum):
    none = "none"
    required = "required"
    approved = "approved"
    escalated = "escalated"


class ActionChannel(str, Enum):
    slack = "slack"
    email = "email"
    workflow = "workflow"
    escalation = "escalation"


class KPI(Base):
    __tablename__ = "kpis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    unit: Mapped[str] = mapped_column(String(24))
    value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(12))
    trend: Mapped[float] = mapped_column(Float, default=0)
    severity: Mapped[Severity] = mapped_column(SqlEnum(Severity), default=Severity.healthy)
    description: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    kpi_key: Mapped[str] = mapped_column(String(64), index=True)
    comparator: Mapped[str] = mapped_column(String(4))
    threshold: Mapped[float] = mapped_column(Float)
    action_channel: Mapped[ActionChannel] = mapped_column(SqlEnum(ActionChannel))
    action_target: Mapped[str] = mapped_column(String(160))
    approval_required: Mapped[bool] = mapped_column(Boolean, default=False)
    message_template: Mapped[str] = mapped_column(Text)
    estimated_value: Mapped[float] = mapped_column(Float, default=0)
    action_cost: Mapped[float] = mapped_column(Float, default=0)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=10)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class ActionEvent(Base):
    __tablename__ = "action_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    rule_name: Mapped[str] = mapped_column(String(160), index=True)
    kpi_key: Mapped[str] = mapped_column(String(64), index=True)
    kpi_value: Mapped[float] = mapped_column(Float)
    channel: Mapped[ActionChannel] = mapped_column(SqlEnum(ActionChannel))
    target: Mapped[str] = mapped_column(String(160))
    status: Mapped[ApprovalState] = mapped_column(SqlEnum(ApprovalState), default=ApprovalState.none)
    message: Mapped[str] = mapped_column(Text)
    estimated_value: Mapped[float] = mapped_column(Float, default=0)
    action_cost: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
