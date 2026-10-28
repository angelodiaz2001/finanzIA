from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..ai import assistant
from ..config import Settings, get_settings
from ..database import get_db
from ..models import Transaction
from ..schemas import CategorizeRequest, CategorizeResponse, ChatRequest, ChatResponse

router = APIRouter(prefix="/assistant", tags=["asistente IA"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db),
         settings: Settings = Depends(get_settings)) -> ChatResponse:
    """Pregunta en lenguaje natural. El modelo consulta los datos consolidados mediante herramientas."""
    return assistant.chat(db, settings, body.message, body.conversation_id)


@router.delete("/chat/{conversation_id}", status_code=204)
def reset(conversation_id: str) -> None:
    assistant.reset_conversation(conversation_id)


@router.post("/categorize", response_model=CategorizeResponse)
def categorize(body: CategorizeRequest, db: Session = Depends(get_db),
               settings: Settings = Depends(get_settings)) -> CategorizeResponse:
    """Sugiere una categoría para una transacción existente o para una descripción libre."""
    tx = None
    description, merchant, tx_type = body.description, body.merchant, body.type
    if body.transaction_id is not None:
        tx = db.get(Transaction, body.transaction_id)
        if tx is None:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
        description, merchant, tx_type = tx.description, tx.merchant, tx.type
    if not description:
        raise HTTPException(status_code=422, detail="Indica transaction_id o description")

    result = assistant.suggest_category(db, settings, description, merchant, tx_type)
    if body.apply and tx is not None:
        tx.category = result.category
        tx.category_source = result.source
        db.commit()
        result.applied = True
    return result
