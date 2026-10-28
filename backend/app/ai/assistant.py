"""Asistente de IA generativa de FinanzIA.

El modelo de lenguaje (Claude, mediante el SDK oficial de Anthropic) NO
calcula cifras: obtiene los datos ya procesados por el backend a través de
herramientas (tool use) y se limita a interpretarlos, explicarlos y sugerir.
Así las respuestas se fundamentan en información consolidada y se reduce el
riesgo de montos inventados por el modelo.

Si no hay credenciales configuradas, el resto de la aplicación sigue
funcionando y el asistente lo indica de forma explícita.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import analytics
from ..categorizer import ALL_CATEGORIES, EXPENSE_CATEGORIES, INCOME_CATEGORIES, categorize
from ..config import Settings
from ..schemas import CategorizeResponse, ChatResponse, ToolCall

try:
    import anthropic
except ImportError:  # pragma: no cover - dependencia opcional en tiempo de ejecución
    anthropic = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

SERVER_FALLBACK_BETA = "server-side-fallback-2026-07-01"

# Conversaciones en memoria (prototipo): conversation_id -> mensajes completos.
# Se guardan los bloques de contenido tal como los devuelve la API para
# reenviarlos sin alterar el historial en turnos posteriores.
_CONVERSATIONS: dict[str, list[dict[str, Any]]] = {}

SYSTEM_PROMPT = """Eres FinanzIA, un asistente de finanzas personales de un prototipo académico.

Tu función es interpretar y explicar la información financiera del usuario: ingresos, gastos, saldos, distribución por categorías y hábitos de consumo. También puedes sugerir ajustes razonables para alcanzar metas de ahorro.

Reglas:
- Todas las cifras provienen de las herramientas disponibles, que consultan datos ya consolidados y calculados por el sistema. Usa las herramientas antes de dar cualquier monto; nunca inventes ni estimes cifras por tu cuenta.
- Si la pregunta menciona un periodo (mes, semana, "últimos 30 días"), tradúcelo a fechas concretas usando la fecha de hoy y pásalas a las herramientas.
- Si no hay datos para lo que se pregunta, dilo claramente.
- Responde en español, de forma breve y clara. Usa el código de moneda que devuelven las herramientas.
- Las "Transferencias internas" son movimientos entre cuentas del propio usuario y no cuentan como ingreso ni gasto.
- Los datos son ficticios y provienen de APIs simuladas; no ofrezcas asesoría de inversión ni recomendaciones de productos financieros concretos.
"""

TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_summary",
        "description": "Resumen financiero de un periodo: ingresos, gastos, balance neto, transferencias internas y conteo por fuente. Sin fechas devuelve el total histórico.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": ["string", "null"], "description": "Fecha inicial YYYY-MM-DD o null"},
                "to_date": {"type": ["string", "null"], "description": "Fecha final YYYY-MM-DD o null"},
            },
            "required": ["from_date", "to_date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_by_category",
        "description": "Totales por categoría (ordenados de mayor a menor) con su participación porcentual, para gastos o ingresos en un periodo.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": ["string", "null"]},
                "to_date": {"type": ["string", "null"]},
                "type": {"type": "string", "enum": ["expense", "income"]},
            },
            "required": ["from_date", "to_date", "type"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_monthly_trend",
        "description": "Ingresos, gastos y balance neto por mes de los últimos N meses.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"months": {"type": "integer", "minimum": 1, "maximum": 24}},
            "required": ["months"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search_transactions",
        "description": "Busca transacciones (ordenadas por importe descendente) filtrando por texto, categoría, tipo y fechas. Útil para ver los mayores gastos o encontrar un comercio.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": ["string", "null"], "description": "Texto a buscar en descripción o comercio"},
                "category": {"type": ["string", "null"]},
                "type": {"type": ["string", "null"], "enum": ["expense", "income", None]},
                "from_date": {"type": ["string", "null"]},
                "to_date": {"type": ["string", "null"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50},
            },
            "required": ["query", "category", "type", "from_date", "to_date", "limit"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_categories",
        "description": "Lista las categorías de gasto e ingreso que usa el sistema y los saldos actuales de las cuentas.",
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
]


def _parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(str(value)[:10])


def execute_tool(db: Session, settings: Settings, name: str, args: dict[str, Any]) -> str:
    """Ejecuta una herramienta contra los datos consolidados y devuelve JSON."""
    if name == "get_summary":
        result: Any = analytics.summary(db, _parse_date(args.get("from_date")), _parse_date(args.get("to_date")),
                                        settings.default_currency)
    elif name == "get_by_category":
        result = analytics.by_category(db, _parse_date(args.get("from_date")), _parse_date(args.get("to_date")),
                                       args.get("type") or "expense")
    elif name == "get_monthly_trend":
        result = analytics.monthly(db, int(args.get("months") or 6))
    elif name == "search_transactions":
        result = analytics.search_transactions(
            db, query=args.get("query") or None, category=args.get("category") or None,
            tx_type=args.get("type") or None, date_from=_parse_date(args.get("from_date")),
            date_to=_parse_date(args.get("to_date")), limit=int(args.get("limit") or 20),
        )
    elif name == "list_categories":
        result = {"expense_categories": EXPENSE_CATEGORIES, "income_categories": INCOME_CATEGORIES,
                  "accounts": analytics.balances(db)}
    else:
        raise ValueError(f"herramienta desconocida: {name}")
    return json.dumps(result, ensure_ascii=False, default=str)


# --------------------------------------------------------------------------- #
# Cliente
# --------------------------------------------------------------------------- #
def credentials_present(settings: Settings) -> bool:
    if settings.anthropic_api_key:
        return True
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    # perfil creado con `ant auth login`
    return (Path.home() / ".config" / "anthropic").exists()


def is_configured(settings: Settings) -> bool:
    return anthropic is not None and credentials_present(settings)


def _client(settings: Settings) -> Any:
    if settings.anthropic_api_key:
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return anthropic.Anthropic()


def _create_message(client: Any, settings: Settings, **kwargs: Any) -> Any:
    """Llama a la API. Activa el fallback de servidor ante rechazos de seguridad si está habilitado."""
    if settings.anthropic_server_fallback:
        try:
            return client.beta.messages.create(betas=[SERVER_FALLBACK_BETA], fallbacks="default", **kwargs)
        except TypeError:
            log.warning("El SDK instalado no soporta fallbacks de servidor; se continúa sin ellos.")
    return client.messages.create(**kwargs)


def _friendly_error(exc: Exception) -> str:
    if anthropic is None:
        return "El SDK de Anthropic no está instalado."
    if isinstance(exc, anthropic.AuthenticationError):
        return "La clave de API de Anthropic no es válida. Revisa ANTHROPIC_API_KEY en el archivo .env."
    if isinstance(exc, anthropic.RateLimitError):
        return "El servicio de IA está limitando las solicitudes. Intenta de nuevo en unos segundos."
    if isinstance(exc, anthropic.APIStatusError):
        return f"El servicio de IA respondió con un error ({exc.status_code})."
    if isinstance(exc, anthropic.APIConnectionError):
        return "No se pudo conectar con el servicio de IA. Verifica la conexión a internet."
    return "Ocurrió un error inesperado al consultar al asistente."


# --------------------------------------------------------------------------- #
# Chat con herramientas
# --------------------------------------------------------------------------- #
def chat(db: Session, settings: Settings, message: str, conversation_id: Optional[str] = None) -> ChatResponse:
    conversation_id = conversation_id or uuid.uuid4().hex
    if not is_configured(settings):
        return ChatResponse(
            reply=("El asistente de IA no está configurado. Define ANTHROPIC_API_KEY en el archivo .env "
                   "del proyecto y reinicia el backend. El resto de FinanzIA (sincronización, "
                   "historial y estadísticas) funciona sin él."),
            conversation_id=conversation_id, model=None, tools_used=[], configured=False,
        )

    messages = _CONVERSATIONS.setdefault(conversation_id, [])
    messages.append({"role": "user", "content": message})
    tools_used: list[ToolCall] = []
    reply = ""

    system_blocks = [
        {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": f"Fecha de hoy: {date.today().isoformat()}. Moneda por defecto: {settings.default_currency}."},
    ]

    try:
        client = _client(settings)
        response = None
        for _ in range(settings.anthropic_max_tool_rounds):
            response = _create_message(
                client, settings,
                model=settings.anthropic_model, max_tokens=16000, system=system_blocks,
                tools=TOOLS, messages=messages, output_config={"effort": settings.anthropic_effort},
            )
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "refusal":
                reply = "No puedo ayudar con esa consulta."
                break

            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if response.stop_reason == "tool_use" and tool_uses:
                results = []
                for tu in tool_uses:
                    args = dict(tu.input or {})
                    tools_used.append(ToolCall(name=tu.name, input=args))
                    try:
                        results.append({"type": "tool_result", "tool_use_id": tu.id,
                                        "content": execute_tool(db, settings, tu.name, args)})
                    except Exception as exc:  # noqa: BLE001 - se informa al modelo, no se oculta
                        log.exception("Error ejecutando herramienta %s", tu.name)
                        results.append({"type": "tool_result", "tool_use_id": tu.id,
                                        "content": f"Error: {exc}", "is_error": True})
                messages.append({"role": "user", "content": results})
                continue

            if response.stop_reason == "pause_turn":
                continue
            break

        if response is not None and not reply:
            reply = "".join(b.text for b in response.content if b.type == "text").strip()
            if response.stop_reason == "max_tokens":
                reply += "\n\n(La respuesta se cortó por longitud.)"
        if not reply:
            reply = "No obtuve una respuesta del modelo. Intenta reformular la pregunta."
    except Exception as exc:  # noqa: BLE001
        log.exception("Fallo en el asistente de IA")
        # Se descarta el turno fallido para no dejar la conversación inconsistente.
        del messages[-1:]
        if messages and messages[-1]["role"] == "user":
            messages.pop()
        reply = _friendly_error(exc)

    return ChatResponse(reply=reply, conversation_id=conversation_id, model=settings.anthropic_model,
                        tools_used=tools_used, configured=True)


def reset_conversation(conversation_id: str) -> bool:
    return _CONVERSATIONS.pop(conversation_id, None) is not None


# --------------------------------------------------------------------------- #
# Sugerencia de categoría (salida estructurada)
# --------------------------------------------------------------------------- #
class CategorySuggestion(BaseModel):
    category: str = Field(description="Exactamente una de las categorías permitidas")
    reason: str = Field(description="Justificación breve en español")
    confidence: float = Field(ge=0, le=1)


def suggest_category(db: Session, settings: Settings, description: str, merchant: Optional[str],
                     tx_type: str) -> CategorizeResponse:
    rule_category, keyword = categorize(description, merchant, tx_type)
    rules_result = CategorizeResponse(
        category=rule_category,
        reason=f"Regla por palabra clave: {keyword}" if keyword else "Sin coincidencia de reglas; categoría por defecto",
        confidence=0.8 if keyword else 0.3, source="rules",
    )
    if not is_configured(settings):
        return rules_result

    allowed = INCOME_CATEGORIES if tx_type == "income" else EXPENSE_CATEGORIES
    prompt = (
        f"Transacción de tipo {tx_type}.\nDescripción: {description!r}\nComercio: {merchant!r}\n"
        f"Elige la categoría más adecuada entre exactamente estas opciones: {allowed}.\n"
        f"La regla automática propuso {rule_category!r}; corrígela solo si otra categoría encaja mejor."
    )
    try:
        client = _client(settings)
        response = client.messages.parse(
            model=settings.anthropic_model, max_tokens=4000, output_config={"effort": "low"},
            system="Clasificas movimientos de finanzas personales en categorías. Responde solo con el objeto pedido.",
            messages=[{"role": "user", "content": prompt}], output_format=CategorySuggestion,
        )
        suggestion = response.parsed_output
        if suggestion is not None and suggestion.category in ALL_CATEGORIES:
            return CategorizeResponse(category=suggestion.category, reason=suggestion.reason,
                                      confidence=suggestion.confidence, source="ai")
    except Exception:  # noqa: BLE001
        log.exception("Fallo al pedir sugerencia de categoría a la IA; se usa la regla")
    return rules_result
