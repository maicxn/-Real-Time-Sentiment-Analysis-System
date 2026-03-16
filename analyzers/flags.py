"""
Detecção de marcações especiais (flags) — funcionário MBRAS, padrão especial e candidate awareness.
"""

import logging

from analyzers.constants import (
    META_PHRASE,
    SPECIAL_PATTERN_LENGTH,
    FlagsResult,
)
from analyzers.text import is_mbras_user

logger = logging.getLogger(__name__)


def compute_flags(messages: list[dict]) -> FlagsResult:
    """
    Avalia as flags especiais por todas as mensagens no feed.

    Flags:
        - ``mbras_employee``: Pelo menos um user_id contém ``"mbras"`` (case-insensitive).
        - ``special_pattern``: Pelo menos um conteúdo possui exatos 42 caracteres Unicode E contém a palavra ``"mbras"``.
        - ``candidate_awareness``: Pelo menos um conteúdo contém ``"teste técnico mbras"``.
    """
    flags: FlagsResult = {
        "mbras_employee": False,
        "special_pattern": False,
        "candidate_awareness": False,
    }

    for msg in messages:
        user_id = msg["user_id"]
        content = msg["content"]
        content_lower = content.lower()

        if is_mbras_user(user_id):
            flags["mbras_employee"] = True

        if len(content) == SPECIAL_PATTERN_LENGTH and "mbras" in content_lower:
            flags["special_pattern"] = True

        if META_PHRASE in content_lower:
            flags["candidate_awareness"] = True

        # Otimização early exit: caso todas atinjam True antes do final
        if all(flags.values()):
            break

    logger.debug("Flags calculadas: %s", flags)
    return flags
