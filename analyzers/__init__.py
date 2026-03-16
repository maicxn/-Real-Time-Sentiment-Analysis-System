"""
Pacote Analyzers MBRAS
Componentes modulares para análise de sentimentos.
"""

from analyzers.constants import (
    GOLDEN_RATIO,
    INTENSIFIER_MULTIPLIER,
    INTENSIFIERS,
    NEGATION_SCOPE,
    NEGATIONS,
    NEGATIVE_WORDS,
    POSITIVE_WORDS,
    SENTIMENT_THRESHOLD,
)
from analyzers.engine import analyze_feed

__all__ = [
    "analyze_feed",
    "POSITIVE_WORDS",
    "NEGATIVE_WORDS",
    "INTENSIFIERS",
    "NEGATIONS",
    "GOLDEN_RATIO",
    "INTENSIFIER_MULTIPLIER",
    "NEGATION_SCOPE",
    "SENTIMENT_THRESHOLD",
]
