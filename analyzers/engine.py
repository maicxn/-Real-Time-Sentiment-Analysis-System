"""
Motor de análise (engine) — orquestra todos os componentes de análise em uma função pura.
"""

import logging
import time
from collections import defaultdict
from datetime import datetime

from analyzers.anomaly import detect_anomalies
from analyzers.constants import (
    CANDIDATE_ENGAGEMENT_OVERRIDE,
    FUTURE_TOLERANCE_SECONDS,
    AnalysisResult,
)
from analyzers.flags import compute_flags
from analyzers.influence import build_influence_ranking
from analyzers.sentiment import compute_sentiment
from analyzers.text import is_mbras_user, now_utc, parse_timestamp
from analyzers.trending import compute_trending

logger = logging.getLogger(__name__)


def analyze_feed(data: dict) -> AnalysisResult:
    """
    Função pura: analisa o feed de mensagens e retorna métricas completas e processadas.

    Este é o ponto de entrada principal que orquestra todos os componentes de análise:
        1. Filtra as mensagens em um futuro impossível
        2. Calcula de flags (marcações passivas extras)
        3. Calcula o sentimento individual
        4. Calcula a distribuição de sentimento
        5. Consolida métricas por autor
        6. Calcula ranqueamento de taxa de engajamento do feed total
        7. Preenche a lista de influenciadores ordenada
        8. Detecta anomalias

    Args:
        data: Payload da requisição Web contendo ``messages`` e ``time_window_minutes``.

    Returns:
        Um dicionário final do tipo ``AnalysisResult``.
    """
    t0 = time.perf_counter()

    messages = data.get("messages", [])
    current_time = now_utc()

    # Etapa 1: Filtra mensagens do futuro fora da nossa margem de tolerância
    filtered = _filter_future_messages(messages, current_time)

    # Etapa 2: Flags passíveis diretas
    flags = compute_flags(filtered)

    # Etapa 3: Calcula o sentimento de capa (message_id -> class)
    sentiments = _compute_all_sentiments(filtered)

    # Etapa 4: Classificação final em % de distribuição percentual (ignorando "meta")
    distribution = _build_distribution(sentiments)

    # Etapa 5: Pontuação geral da taxa de engajamento do período todo
    engagement_score = _compute_engagement(filtered, flags)

    # Etapa 6: Ranking total de engajamentos e influência pura baseada em autores logados
    influence_ranking = _build_user_influence(filtered)

    # Etapa 7: Cálculo ponderado de peso dos temas da hora com hashtags
    trending = compute_trending(filtered, sentiments, current_time)

    # Etapa 8: Validações finais de proteção a spoofing via regras numéricas por volume/ciclo
    anomaly_detected, anomaly_type = detect_anomalies(filtered, sentiments)

    elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

    logger.info(
        "Feed analisado: %d mensagens, %.2fms, sentimento=%s",
        len(filtered),
        elapsed_ms,
        distribution,
    )

    return {
        "sentiment_distribution": distribution,
        "engagement_score": engagement_score,
        "trending_topics": trending,
        "influence_ranking": influence_ranking,
        "anomaly_detected": anomaly_detected,
        "anomaly_type": anomaly_type,
        "flags": flags,
        "processing_time_ms": elapsed_ms,
    }


# ─────────────────────── Funções Auxiliares ───────────────────────


def _filter_future_messages(
    messages: list[dict],
    current_time: datetime,
) -> list[dict]:
    """Rejeita mensagens com timestamps além de FUTURE_TOLERANCE_SECONDS no futuro."""
    filtered = []
    for msg in messages:
        ts = parse_timestamp(msg["timestamp"])
        if (ts - current_time).total_seconds() > FUTURE_TOLERANCE_SECONDS:
            continue
        filtered.append(msg)
    return filtered


def _compute_all_sentiments(messages: list[dict]) -> dict[str, str]:
    """Calcula a classificação de sentimento para todas as mensagens."""
    sentiments: dict[str, str] = {}
    for msg in messages:
        msg_is_mbras = is_mbras_user(msg["user_id"])
        _, classification = compute_sentiment(msg["content"], msg_is_mbras)
        sentiments[msg["id"]] = classification
    return sentiments


def _build_distribution(sentiments: dict[str, str]) -> dict[str, float]:
    """Calcula a distribuição percentual excluindo o meta-sentimento."""
    pos = sum(1 for s in sentiments.values() if s == "positive")
    neg = sum(1 for s in sentiments.values() if s == "negative")
    neu = sum(1 for s in sentiments.values() if s == "neutral")
    total = pos + neg + neu

    if total > 0:
        return {
            "positive": round(pos / total * 100, 1),
            "negative": round(neg / total * 100, 1),
            "neutral": round(neu / total * 100, 1),
        }
    return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}


def _compute_engagement(messages: list[dict], flags: dict) -> float:
    """Calcula o engagement_score global com superposição de candidate_awareness."""
    if flags["candidate_awareness"]:
        return CANDIDATE_ENGAGEMENT_OVERRIDE

    total_reactions = sum(m.get("reactions", 0) for m in messages)
    total_shares = sum(m.get("shares", 0) for m in messages)
    total_views = max(sum(m.get("views", 0) for m in messages), 1)

    return round((total_reactions + total_shares) / total_views, 4)


def _build_user_influence(messages: list[dict]) -> list[dict]:
    """Agrega estatísticas por usuário e constrói o ranking de influência."""
    user_stats: dict[str, dict] = defaultdict(
        lambda: {"reactions": 0, "shares": 0, "views": 0, "is_mbras": False}
    )

    for msg in messages:
        uid = msg["user_id"]
        user_stats[uid]["reactions"] += msg.get("reactions", 0)
        user_stats[uid]["shares"] += msg.get("shares", 0)
        user_stats[uid]["views"] += msg.get("views", 0)
        user_stats[uid]["is_mbras"] = is_mbras_user(uid)

    return build_influence_ranking(user_stats)
