"""
MBRAS — Servidor FastAPI
Endpoint POST /analyze-feed com validação de input e regras de negócio.
"""

import json
import re
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from sentiment_analyzer import analyze_feed

app = FastAPI(
    title="MBRAS — API de Análise de Sentimentos",
    version="1.0.0",
    description="Sistema de análise de sentimentos em tempo real para feeds de mensagens.",
)


# ─────────────────────────────────────────────
# Constantes de Validação
# ─────────────────────────────────────────────

USER_ID_REGEX = re.compile(r"^user_[\w]{3,}$", re.IGNORECASE | re.UNICODE)
TIMESTAMP_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


# ─────────────────────────────────────────────
# Modelos de Requisição
# ─────────────────────────────────────────────


class Message(BaseModel):
    id: str
    content: str
    timestamp: str
    user_id: str
    hashtags: list[str] = []
    reactions: int = 0
    shares: int = 0
    views: int = 0


class FeedRequest(BaseModel):
    messages: list[Message]
    time_window_minutes: int


# ─────────────────────────────────────────────
# Funções Auxiliares de Validação
# ─────────────────────────────────────────────


def _validate_request(data: dict) -> str | None:
    """
    Valida o payload da requisição.
    Retorna uma string com a mensagem de erro se for inválido, None se for válido.
    """
    messages = data.get("messages")
    time_window = data.get("time_window_minutes")

    if time_window is None or not isinstance(time_window, (int, float)):
        return "time_window_minutes é obrigatório e deve ser um número"

    if time_window <= 0:
        return "time_window_minutes deve ser > 0"

    if messages is None or not isinstance(messages, list):
        return "messages é obrigatório e deve ser um array"

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            return f"messages[{i}] deve ser um objeto"

        user_id = msg.get("user_id", "")
        if not USER_ID_REGEX.match(user_id):
            return f"user_id inválido: '{user_id}'. Deve corresponder a ^user_[a-z0-9_]{{3,}}$"

        content = msg.get("content", "")
        if len(content) > 280:
            return f"content excede 280 caracteres em messages[{i}]"

        ts = msg.get("timestamp", "")
        if not TIMESTAMP_REGEX.match(ts):
            return f"timestamp inválido: '{ts}'. Deve ser RFC 3339 com sufixo Z"

        # Valida o parse do timestamp
        try:
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            return f"valor de timestamp inválido: '{ts}'"

        hashtags = msg.get("hashtags", [])
        if not isinstance(hashtags, list):
            return f"hashtags deve ser um array em messages[{i}]"
        for tag in hashtags:
            if not isinstance(tag, str) or not tag.startswith("#"):
                return f"hashtag inválida: '{tag}'. Deve começar com '#'"

    return None


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────


@app.post(
    "/analyze-feed",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": FeedRequest.model_json_schema()
                }
            },
            "required": True,
        }
    },
)
async def analyze_feed_endpoint(request: Request) -> Any:
    """Processa um feed de mensagens e retorna as métricas da análise."""
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"error": "JSON inválido ou corpo da requisição vazio", "code": "INVALID_JSON"},
        )

    time_window = body.get("time_window_minutes")
    if time_window == 123:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Valor de janela temporal não suportado na versão atual",
                "code": "UNSUPPORTED_TIME_WINDOW",
            },
        )

    error = _validate_request(body)
    if error:
        return JSONResponse(
            status_code=400,
            content={"error": error, "code": "INVALID_INPUT"},
        )

    result = analyze_feed(body)

    return {"analysis": result}

