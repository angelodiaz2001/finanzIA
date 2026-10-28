"""Modelo de datos consolidado de FinanzIA (estructura común para todas las fuentes)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


class Account(Base):
    """Cuenta bancaria o billetera, con su saldo más reciente."""

    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_accounts_source_external"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(20), index=True)          # bank | wallet
    external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(120))
    account_type: Mapped[str] = mapped_column(String(30))
    currency: Mapped[str] = mapped_column(String(3))
    balance: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class Transaction(Base):
    """Movimiento normalizado. amount siempre positivo; type indica el sentido."""

    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_transactions_source_external"),
        Index("ix_transactions_dedup", "type", "amount", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(20), index=True)          # bank | wallet | notification
    external_id: Mapped[str] = mapped_column(String(64))
    occurred_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    amount: Mapped[float] = mapped_column(Numeric(14, 2, asdecimal=False))
    type: Mapped[str] = mapped_column(String(10))                        # income | expense
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String(255))
    merchant: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    category_source: Mapped[str] = mapped_column(String(20), default="rules")  # rules | ai | manual
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    duplicate_of_id: Mapped[Optional[int]] = mapped_column(ForeignKey("transactions.id"), nullable=True)
    raw: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class SyncRun(Base):
    """Registro de cada ejecución de sincronización con las fuentes."""

    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="running")   # running | ok | partial | error
    report: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
