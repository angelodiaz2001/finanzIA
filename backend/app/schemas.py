"""Esquemas Pydantic (entrada/salida) del backend principal."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Source = Literal["bank", "wallet", "notification"]
TxType = Literal["income", "expense"]


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    name: str
    account_type: str
    currency: str
    balance: float
    updated_at: datetime


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    occurred_at: datetime
    amount: float
    type: str
    currency: str
    description: str
    merchant: Optional[str] = None
    category: str
    category_source: str
    is_duplicate: bool
    duplicate_of_id: Optional[int] = None
    created_at: datetime


class TransactionDetail(TransactionOut):
    raw: Optional[dict[str, Any]] = None


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class CategoryUpdate(BaseModel):
    category: str = Field(min_length=2, max_length=60)


class SourceCount(BaseModel):
    bank: int = 0
    wallet: int = 0
    notification: int = 0


class SyncReport(BaseModel):
    run_id: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    fetched: SourceCount
    inserted: SourceCount
    duplicates_exact: int = 0
    duplicates_cross: int = 0
    skipped: int = 0
    rejected: int = 0
    errors: list[str] = Field(default_factory=list, description="Fuentes que no respondieron")
    warnings: list[str] = Field(default_factory=list, description="Registros rechazados por validación")


class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    report: Optional[dict[str, Any]] = None


class SourceSummary(BaseModel):
    source: str
    count: int
    income: float
    expenses: float


class Summary(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    currency: str
    income: float
    expenses: float
    net: float
    internal_transfers: float
    count: int
    duplicates_detected: int
    by_source: list[SourceSummary]


class CategoryShare(BaseModel):
    category: str
    type: str
    total: float
    count: int
    share: float


class MonthPoint(BaseModel):
    month: str
    income: float
    expenses: float
    net: float


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ToolCall(BaseModel):
    name: str
    input: dict[str, Any]


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    model: Optional[str] = None
    tools_used: list[ToolCall] = Field(default_factory=list)
    configured: bool


class CategorizeRequest(BaseModel):
    transaction_id: Optional[int] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    type: TxType = "expense"
    apply: bool = Field(default=False, description="Si es true y hay transaction_id, guarda la categoría sugerida")


class CategorizeResponse(BaseModel):
    category: str
    reason: str
    confidence: float
    source: Literal["ai", "rules"]
    applied: bool = False


class HealthOut(BaseModel):
    status: str
    database: str
    sources: dict[str, str]
    ai_configured: bool
