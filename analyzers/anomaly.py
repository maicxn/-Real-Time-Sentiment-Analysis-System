"""
Detecção de anomalias — padrões de burst (explosão), alternância e postagens sincronizadas.
"""

import logging
from collections import defaultdict
from datetime import datetime

from analyzers.constants import (
    ALTERNATION_MIN_MESSAGES,
    BURST_THRESHOLD,
    BURST_WINDOW_SECONDS,
    SYNC_MIN_MESSAGES,
    SYNC_WINDOW_SECONDS,
)
from analyzers.text import parse_timestamp

logger = logging.getLogger(__name__)


def detect_anomalies(
    messages: list[dict],
    sentiments: dict[str, str],
) -> tuple[bool, str | None]:
    """
    Detecta anomalias comportamentais no feed de mensagens.

    Regras testadas (nesta ordem):
        1. **Burst**: >10 mensagens do mesmo usuário em menos de 5 minutos.
        2. **Alternância**: Padrão de sentimento exato ``+−+−`` em ≥10 mensagens por usuário.
        3. **Postagem sincronizada**: ≥3 mensagens dentro de uma margem de ±2 segundos.
    """
    if not messages:
        return False, None

    user_times, all_times = _group_timestamps(messages)

    # Regra 1: Detecção de Burst
    if _detect_burst(user_times):
        logger.info("Anomalia detectada: burst")
        return True, "burst"

    # Regra 2: Detecção de Alternância
    if _detect_alternation(messages, sentiments):
        logger.info("Anomalia detectada: alternation")
        return True, "alternation"

    # Regra 3: Postagem sincronizada
    if _detect_synchronized(all_times):
        logger.info("Anomalia detectada: synchronized_posting")
        return True, "synchronized_posting"

    return False, None


# ─────────────────────── Funções Auxiliares ───────────────────────


def _group_timestamps(
    messages: list[dict],
) -> tuple[dict[str, list[datetime]], list[datetime]]:
    """Faz o parse e agrupa os timestamps por usuário, além de uma lista total."""
    user_times: dict[str, list[datetime]] = defaultdict(list)
    all_times: list[datetime] = []

    for msg in messages:
        ts = parse_timestamp(msg["timestamp"])
        user_times[msg["user_id"]].append(ts)
        all_times.append(ts)

    return user_times, all_times


def _detect_burst(user_times: dict[str, list[datetime]]) -> bool:
    """Verifica se algum usuário enviou > BURST_THRESHOLD mensagens em BURST_WINDOW."""
    for times in user_times.values():
        times_sorted = sorted(times)
        for i in range(len(times_sorted)):
            count = 1
            for j in range(i + 1, len(times_sorted)):
                if (times_sorted[j] - times_sorted[i]).total_seconds() <= BURST_WINDOW_SECONDS:
                    count += 1
                else:
                    break
            if count > BURST_THRESHOLD:
                return True
    return False


def _detect_alternation(
    messages: list[dict],
    sentiments: dict[str, str],
) -> bool:
    """Verifica o padrão exato de alternância positiva-negativa em ≥ N mensagens mensais do user."""
    user_sentiments: dict[str, list[str]] = defaultdict(list)

    for msg in messages:
        s = sentiments.get(msg["id"], "neutral")
        if s in ("positive", "negative"):
            user_sentiments[msg["user_id"]].append(s)

    for sents in user_sentiments.values():
        if len(sents) >= ALTERNATION_MIN_MESSAGES:
            is_alternating = all(
                sents[i] != sents[i - 1] for i in range(1, len(sents))
            )
            if is_alternating:
                return True
    return False


def _detect_synchronized(all_times: list[datetime]) -> bool:
    """Verifica se há ≥ SYNC_MIN_MESSAGES dentro de ± SYNC_WINDOW_SECONDS."""
    if len(all_times) < SYNC_MIN_MESSAGES:
        return False

    sorted_times = sorted(all_times)
    for i in range(len(sorted_times)):
        count = 1
        for j in range(i + 1, len(sorted_times)):
            if (sorted_times[j] - sorted_times[i]).total_seconds() <= SYNC_WINDOW_SECONDS:
                count += 1
            else:
                break
        if count >= SYNC_MIN_MESSAGES:
            return True
    return False
