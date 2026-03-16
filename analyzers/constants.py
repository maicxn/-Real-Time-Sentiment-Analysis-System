"""
Constantes nomeadas para o motor de análise.
Elimina números mágicos e centraliza a configuração.
"""

import math
from typing import TypedDict


# ─────────────────────────────── Léxico ───────────────────────────────

POSITIVE_WORDS: frozenset[str] = frozenset(
    {
        "adorei",
        "gostei",
        "excelente",
        "otimo",
        "perfeito",
        "bom",
        "maravilhoso",
        "incrivel",
        "fantastico",
        "sensacional",
        "top",
    }
)

NEGATIVE_WORDS: frozenset[str] = frozenset(
    {
        "ruim",
        "terrivel",
        "pessimo",
        "horrivel",
        "odiei",
        "detestei",
        "nojento",
        "decepcionante",
    }
)

INTENSIFIERS: frozenset[str] = frozenset(
    {
        "muito",
        "super",
        "extremamente",
        "bastante",
        "demais",
        "incrivelmente",
        "absurdamente",
    }
)

NEGATIONS: frozenset[str] = frozenset(
    {
        "nao",
        "nunca",
        "jamais",
        "nem",
        "tampouco",
    }
)


# ─────────────────────────── Regras de Sentimento ───────────────────────────

INTENSIFIER_MULTIPLIER: float = 1.5
"""Fator aplicado quando um intensificador precede uma palavra de polaridade."""

NEGATION_SCOPE: int = 3
"""Número de tokens à frente que uma negação pode afetar."""

SENTIMENT_THRESHOLD: float = 0.1
"""Pontuação acima → positivo; abaixo → negativo; caso contrário → neutro."""

MBRAS_SENTIMENT_MULTIPLIER: float = 2.0
"""Multiplicador para pontuações positivas quando o usuário é funcionário MBRAS."""

META_PHRASE: str = "teste técnico mbras"
"""Frase exata (case-insensitive) que aciona o meta-sentimento."""


# ─────────────────────────── Regras de Influência ───────────────────────────

GOLDEN_RATIO: float = (1 + math.sqrt(5)) / 2
"""φ ≈ 1.618 — usado para ajuste de engajamento."""

FOLLOWERS_WEIGHT: float = 0.4
"""Peso dos seguidores na fórmula de pontuação de influência."""

ENGAGEMENT_WEIGHT: float = 0.6
"""Peso do engajamento na fórmula de pontuação de influência."""

GOLDEN_RATIO_INTERACTION_MOD: int = 7
"""Interações múltiplas deste número acionam o ajuste do Golden Ratio (Proporção Áurea)."""

PENALTY_007_FACTOR: float = 0.5
"""Fator de penalidade para user_ids terminando em '007'."""

MBRAS_BONUS: float = 2.0
"""Bônus adicionado à pontuação de influência para funcionários MBRAS."""

UNICODE_FOLLOWERS: int = 4242
"""Contagem fixa de seguidores para user_ids com diacríticos (acentos)."""

FIBONACCI_FOLLOWERS: int = 233
"""Contagem fixa de seguidores para user_ids de 13 caracteres (13º Fibonacci)."""

FIBONACCI_LENGTH: int = 13
"""Limite de tamanho de user_id para a regra de seguidores de Fibonacci."""

FOLLOWER_MOD: int = 10000
"""Módulo para o cálculo de seguidores usando SHA-256."""

FOLLOWER_BASE: int = 100
"""Base adicionada após o módulo para o cálculo de seguidores usando SHA-256."""


# ─────────────────────────── Regras de Trending ────────────────────────────

TRENDING_TOP_N: int = 5
"""Número de principais hashtags nos trending topics a retornar."""

POSITIVE_SENTIMENT_MOD: float = 1.2
"""Multiplicador de peso para hashtags de sentimento positivo."""

NEGATIVE_SENTIMENT_MOD: float = 0.8
"""Multiplicador de peso para hashtags de sentimento negativo."""

LONG_HASHTAG_THRESHOLD: int = 8
"""Hashtags mais longas que isso recebem um fator de decaimento logarítmico."""


# ─────────────────────────── Regras de Anomalia ─────────────────────────────

BURST_THRESHOLD: int = 10
"""Número de mensagens do mesmo usuário em uma janela para acionar burst."""

BURST_WINDOW_SECONDS: int = 300
"""Janela de tempo (5 minutos) para detecção de burst."""

ALTERNATION_MIN_MESSAGES: int = 10
"""Mínimo de mensagens com padrão alternado para acionar anomalia."""

SYNC_MIN_MESSAGES: int = 3
"""Mínimo de mensagens na janela de sincronia para acionar anomalia."""

SYNC_WINDOW_SECONDS: int = 2
"""Tolerância de tempo para detecção de postagens sincronizadas."""


# ─────────────────────────── Regras de Flags ────────────────────────────────

SPECIAL_PATTERN_LENGTH: int = 42
"""Contagem exata de caracteres Unicode para a flag special_pattern."""

FUTURE_TOLERANCE_SECONDS: int = 5
"""Máximo de segundos futuros aceitos na data da mensagem."""

CANDIDATE_ENGAGEMENT_OVERRIDE: float = 9.42
"""Pontuação de engajamento fixa quando candidate_awareness é True."""


# ─────────────────────────── Estruturas Tipadas ──────────────────────────


class SentimentDistribution(TypedDict):
    """Distribuição percentual das classificações de sentimento."""

    positive: float
    negative: float
    neutral: float


class UserInfluence(TypedDict):
    """Entrada da pontuação de influência para um único usuário."""

    user_id: str
    influence_score: float


class FlagsResult(TypedDict):
    """Flags especiais de detecção."""

    mbras_employee: bool
    special_pattern: bool
    candidate_awareness: bool


class AnalysisResult(TypedDict):
    """Resposta completa da análise."""

    sentiment_distribution: SentimentDistribution
    engagement_score: float
    trending_topics: list[str]
    influence_ranking: list[UserInfluence]
    anomaly_detected: bool
    anomaly_type: str | None
    flags: FlagsResult
    processing_time_ms: float
