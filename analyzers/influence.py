"""
Pontuação de influência de usuário — SHA-256 determinístico e métricas de engajamento.
"""

import hashlib
import logging

from analyzers.constants import (
    ENGAGEMENT_WEIGHT,
    FIBONACCI_FOLLOWERS,
    FIBONACCI_LENGTH,
    FOLLOWER_BASE,
    FOLLOWER_MOD,
    GOLDEN_RATIO,
    GOLDEN_RATIO_INTERACTION_MOD,
    FOLLOWERS_WEIGHT,
    MBRAS_BONUS,
    PENALTY_007_FACTOR,
    UNICODE_FOLLOWERS,
    UserInfluence,
)
from analyzers.text import has_diacritics

logger = logging.getLogger(__name__)


def compute_followers(user_id: str) -> int:
    """
    Calcula a contagem determinística de seguidores para um usuário.

    Casos especiais (verificados nesta ordem):
        1. user_ids Unicode com acentos → fixado em 4242
        2. Exatamente 13 caracteres → 233 (13º número de Fibonacci)
        3. Termina em ``_prime`` → soma dos N primeiros primos (N = tamanho_da_string)
        4. Padrão → ``(SHA-256 % 10000) + 100``
    """
    if has_diacritics(user_id):
        return UNICODE_FOLLOWERS

    if len(user_id) == FIBONACCI_LENGTH:
        return FIBONACCI_FOLLOWERS

    if user_id.endswith("_prime"):
        return sum(_first_n_primes(len(user_id)))

    digest = hashlib.sha256(user_id.encode()).hexdigest()
    return (int(digest, 16) % FOLLOWER_MOD) + FOLLOWER_BASE


def compute_influence(
    user_id: str,
    total_reactions: int,
    total_shares: int,
    total_views: int,
    is_mbras: bool,
) -> float:
    """
    Calcula a pontuação de influência para um único usuário.
    """
    followers = compute_followers(user_id)

    views = max(total_views, 1)
    interactions = total_reactions + total_shares
    engagement_rate = interactions / views

    # Ajuste do Golden Ratio se as interações forem múltiplas de 7
    if interactions > 0 and interactions % GOLDEN_RATIO_INTERACTION_MOD == 0:
        engagement_rate *= 1 + 1 / GOLDEN_RATIO

    score = (followers * FOLLOWERS_WEIGHT) + (engagement_rate * ENGAGEMENT_WEIGHT)

    # Penalidade para user_ids terminando em "007"
    if user_id.endswith("007"):
        score *= PENALTY_007_FACTOR

    # Bônus de funcionário MBRAS
    if is_mbras:
        score += MBRAS_BONUS

    logger.debug(
        "Influência de %s: seguidores=%d, engajamento=%.4f, score=%.4f",
        user_id,
        followers,
        engagement_rate,
        score,
    )

    return round(score, 4)


def build_influence_ranking(
    user_stats: dict[str, dict],
) -> list[UserInfluence]:
    """
    Constrói um ranking ordenado de influência com base no resumo agregado dos usuários.

    Args:
        user_stats: Mapa com user_id → {reactions, shares, views, is_mbras}.

    Returns:
        Lista de dicionários ``UserInfluence``, ordenados pela pontuação (decrescente).
    """
    ranking: list[UserInfluence] = []

    for uid, stats in user_stats.items():
        score = compute_influence(
            uid,
            stats["reactions"],
            stats["shares"],
            stats["views"],
            stats["is_mbras"],
        )
        ranking.append({"user_id": uid, "influence_score": score})

    ranking.sort(key=lambda x: -x["influence_score"])
    return ranking


# ─────────────────────── Funções Auxiliares ───────────────────────


def _first_n_primes(n: int) -> list[int]:
    """Retorna os primeiros *n* números primos usando tentativa por divisão."""
    primes: list[int] = []
    candidate = 2
    while len(primes) < n:
        if all(candidate % p != 0 for p in primes):
            primes.append(candidate)
        candidate += 1
    return primes
