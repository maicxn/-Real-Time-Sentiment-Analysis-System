"""
Análise de sentimento baseada em léxico com intensificadores, negação e regras MBRAS.
"""

import logging

from analyzers.constants import (
    INTENSIFIER_MULTIPLIER,
    INTENSIFIERS,
    MBRAS_SENTIMENT_MULTIPLIER,
    META_PHRASE,
    NEGATION_SCOPE,
    NEGATIONS,
    NEGATIVE_WORDS,
    POSITIVE_WORDS,
    SENTIMENT_THRESHOLD,
)
from analyzers.text import normalize_nfkd, tokenize

logger = logging.getLogger(__name__)


def classify_score(score: float) -> str:
    """
    Classifica uma pontuação de sentimento normalizada.

    Retorna:
        ``"positive"`` se score > limiar,
        ``"negative"`` se score < -limiar,
        ``"neutral"`` caso contrário.
    """
    if score > SENTIMENT_THRESHOLD:
        return "positive"
    if score < -SENTIMENT_THRESHOLD:
        return "negative"
    return "neutral"


def compute_sentiment(content: str, is_mbras: bool) -> tuple[float, str]:
    """
    Calcula a pontuação de sentimento e a classificação para uma única mensagem.

    Pipeline (ordem estrita):
        1. Verifica meta-sentimento (correspondência exata de frase)
        2. Tokeniza e filtra hashtags
        3. Aplica intensificadores (×1.5 na próxima palavra de polaridade)
        4. Aplica negações (escopo de 3 tokens, baseado em paridade)
        5. Aplica regra MBRAS (×2 para pontuações positivas)
        6. Normaliza pela quantidade de tokens e classifica
    """
    # Passo 0: Meta-sentimento tem precedência absoluta
    if content.strip().lower() == META_PHRASE:
        logger.debug("Meta-sentimento detectado: '%s'", content)
        return 0.0, "meta"

    tokens = tokenize(content)
    if not tokens:
        return 0.0, "neutral"

    # Filtra hashtags — elas não carregam sentimento
    lexicon_tokens = [t for t in tokens if not t.startswith("#")]
    if not lexicon_tokens:
        return 0.0, "neutral"

    normalized = [normalize_nfkd(t) for t in lexicon_tokens]
    n_tokens = len(lexicon_tokens)

    # Identifica o papel dos tokens
    is_intensifier = [n in INTENSIFIERS for n in normalized]
    is_negation = [n in NEGATIONS for n in normalized]

    # Pontuações base de polaridade
    scores = [0.0] * n_tokens
    for i, norm in enumerate(normalized):
        if norm in POSITIVE_WORDS:
            scores[i] = 1.0
        elif norm in NEGATIVE_WORDS:
            scores[i] = -1.0

    # Passo 1: Intensificadores — amplifica a próxima palavra de polaridade (×1.5)
    _apply_intensifiers(scores, is_intensifier, n_tokens)

    # Passo 2: Negações — escopo de 3 tokens, paridade determina inversão
    _apply_negations(scores, is_negation, n_tokens)

    # Passo 3: Regra MBRAS — dobra pontuações positivas para funcionários MBRAS
    if is_mbras:
        _apply_mbras_rule(scores)

    total = sum(scores)
    score = total / n_tokens
    classification = classify_score(score)

    logger.debug(
        "Sentimento para '%s': score=%.3f → %s (mbras=%s)",
        content, score, classification, is_mbras,
    )

    return score, classification


# ─────────────────────── Funções Auxiliares ───────────────────────


def _apply_intensifiers(
    scores: list[float],
    is_intensifier: list[bool],
    n_tokens: int,
) -> None:
    """Multiplica a próxima palavra de polaridade pelo fator de intensificação."""
    for i in range(n_tokens):
        if is_intensifier[i]:
            for j in range(i + 1, n_tokens):
                if scores[j] != 0.0:
                    scores[j] *= INTENSIFIER_MULTIPLIER
                    break


def _apply_negations(
    scores: list[float],
    is_negation: list[bool],
    n_tokens: int,
) -> None:
    """Aplica negação baseada em paridade em um escopo de N tokens à frente."""
    negation_counts = [0] * n_tokens
    for i in range(n_tokens):
        if is_negation[i]:
            for j in range(i + 1, min(i + 1 + NEGATION_SCOPE, n_tokens)):
                negation_counts[j] += 1

    for i in range(n_tokens):
        if negation_counts[i] % 2 == 1:  # Ímpar → inverte
            scores[i] *= -1


def _apply_mbras_rule(scores: list[float]) -> None:
    """Dobra todas as pontuações positivas para funcionários MBRAS."""
    for i in range(len(scores)):
        if scores[i] > 0:
            scores[i] *= MBRAS_SENTIMENT_MULTIPLIER
