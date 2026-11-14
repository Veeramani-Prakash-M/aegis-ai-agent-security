from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    provider: Mapped[str] = mapped_column(String(80), default="Local simulator")
    mode: Mapped[str] = mapped_column(String(20), default="hardened")
    allow_tools: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    runs: Mapped[list["EvaluationRun"]] = relationship(back_populates="agent")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    attack_success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    blocked: Mapped[int] = mapped_column(Integer, nullable=False)
    vulnerable: Mapped[int] = mapped_column(Integer, nullable=False)
    results_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    agent: Mapped[Agent] = relationship(back_populates="runs")
