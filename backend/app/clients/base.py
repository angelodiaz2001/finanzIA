from __future__ import annotations

from typing import Any

import httpx


class SourceUnavailable(Exception):
    """La fuente no respondió o devolvió un error."""


def get_json(base_url: str, path: str, params: dict[str, Any] | None = None, timeout: float = 10.0) -> Any:
    url = base_url.rstrip("/") + path
    try:
        resp = httpx.get(url, params=params, timeout=timeout)
    except httpx.HTTPError as exc:
        raise SourceUnavailable(f"No se pudo conectar con {url} ({exc.__class__.__name__})") from exc
    if resp.status_code >= 400:
        raise SourceUnavailable(f"{url} respondió {resp.status_code}: {resp.text[:200]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise SourceUnavailable(f"{url} devolvió una respuesta que no es JSON") from exc


def ping(base_url: str, timeout: float = 2.0) -> str:
    try:
        resp = httpx.get(base_url.rstrip("/") + "/health", timeout=timeout)
        return "ok" if resp.status_code == 200 else f"error {resp.status_code}"
    except httpx.HTTPError:
        return "down"
