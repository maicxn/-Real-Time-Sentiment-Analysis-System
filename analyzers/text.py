"""
Utilitários de processamento de texto.
Tokenização, normalização e parse de timestamps.
"""

import re
import unicodedata
from datetime import datetime, timezone


# Regex compilada — evita recompilação a cada chamada.
_TOKEN_RE = re.compile(r"(?:#\w+(?:-\w+)*)|\b\w+\b", re.UNICODE)


def normalize_nfkd(text: str) -> str:
    """
    Normaliza o texto para equivalência case-insensitive e accent-insensitive no léxico.

    Pipeline: minúsculas → decomposição NFKD → remover marcas combinantes (acentos).
    """
    lowered = text.lower()
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def tokenize(content: str) -> list[str]:
    """
    Divide o conteúdo em tokens seguindo a especificação determinística.

    - Hashtags como ``#produto-novo`` são mantidas como tokens únicos.
    - Pontuação (``!?.,``) é removida.
    - Cada limite de palavra produz um token separado.
    """
    return _TOKEN_RE.findall(content)


def has_diacritics(text: str) -> bool:
    """Retorna ``True`` se o *text* contém marcas diacríticas (acentos) após NFKD."""
    decomposed = unicodedata.normalize("NFKD", text)
    return any(unicodedata.category(ch) == "Mn" for ch in decomposed)


def parse_timestamp(raw: str) -> datetime:
    """
    Faz o parse de um timestamp RFC 3339 com sufixo obrigatório ``Z``.
    """
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def is_mbras_user(user_id: str) -> bool:
    """Verifica se um user_id pertence a um funcionário MBRAS (case-insensitive)."""
    return "mbras" in user_id.lower()


def now_utc() -> datetime:
    """Retorna o timestamp UTC atual."""
    return datetime.now(timezone.utc)
