"""
Trending topics — ranking ponderado de hashtags com fatores temporal, de sentimento e de tamanho.
"""

import logging
import math
from collections import defaultdict
from datetime import datetime

from analyzers.constants import (
    LONG_HASHTAG_THRESHOLD,
    NEGATIVE_SENTIMENT_MOD,
    POSITIVE_SENTIMENT_MOD,
    TRENDING_TOP_N,
)
from analyzers.text import parse_timestamp

logger = logging.getLogger(__name__)

# Mapa de modificadores de sentimento (evita cadeias repetidas de if/elif)
_SENTIMENT_MODIFIERS: dict[str, float] = {
    "positive": POSITIVE_SENTIMENT_MOD,
    "negative": NEGATIVE_SENTIMENT_MOD,
    "neutral": 1.0,
}


def compute_trending(
    messages: list[dict],
    sentiments: dict[str, str],
    now_utc: datetime,
) -> list[str]:
    """
    Calcula o top-N trending topics de hashtags.

    Peso por ocorrência de hashtag:
        ``temporal_weight × sentiment_modifier × long_hashtag_factor``

    Ordem de desempate:
        1. Peso total (decrescente)
        2. Frequência / contagem bruta (decrescente)
        3. Soma do peso de sentimento (decrescente)
        4. Ordem lexicográfica / alfabética (crescente)
    """
    hashtag_data: dict[str, dict] = defaultdict(
        lambda: {"weight_sum": 0.0, "count": 0, "sentiment_weight": 0.0}
    )

    for msg in messages:
        sentiment = sentiments.get(msg["id"], "neutral")
        if sentiment == "meta":
            continue

        ts = parse_timestamp(msg["timestamp"])
        delta_minutes = max((now_utc - ts).total_seconds() / 60, 0.01)
        temporal_weight = 1 + (1 / delta_minutes)

        sentiment_mod = _SENTIMENT_MODIFIERS.get(sentiment, 1.0)

        for tag in msg.get("hashtags", []):
            log_factor = _long_hashtag_factor(tag)
            weight = temporal_weight * sentiment_mod * log_factor

            hashtag_data[tag]["weight_sum"] += weight
            hashtag_data[tag]["count"] += 1
            hashtag_data[tag]["sentiment_weight"] += sentiment_mod

    sorted_tags = sorted(
        hashtag_data.keys(),
        key=lambda t: (
            -hashtag_data[t]["weight_sum"],
            -hashtag_data[t]["count"],
            -hashtag_data[t]["sentiment_weight"],
            t,
        ),
    )

    result = sorted_tags[:TRENDING_TOP_N]
    logger.debug("Trending topics (top %d): %s", TRENDING_TOP_N, result)
    return result


# ─────────────────────── Funções Auxiliares ───────────────────────


def _long_hashtag_factor(tag: str) -> float:
    """
    Calcula o fator de decaimento logarítmico para hashtags longas.

    Hashtags com tamanho > 8 recebem fator de ``log₁₀(tamanho) / log₁₀(8)``.
    Hashtags mais curtas recebem fator de 1.0 (sem ajuste).
    """
    tag_len = len(tag)
    if tag_len > LONG_HASHTAG_THRESHOLD:
        return math.log10(tag_len) / math.log10(LONG_HASHTAG_THRESHOLD)
    return 1.0
