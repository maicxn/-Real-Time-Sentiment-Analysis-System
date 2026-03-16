"""
MBRAS — Motor de Análise de Sentimentos (facade).

Este módulo reexporta ``analyze_feed`` do pacote modular ``analyzers``
para manter a retrocompatibilidade com o ``main.py`` e os testes.

Arquitetura::

    sentiment_analyzer.py  (esta fachada)
        └── analyzers/
            ├── constants.py   — constantes nomeadas & tipagens TypedDict
            ├── text.py        — tokenização, normalização, parse de timestamp
            ├── sentiment.py   — pontuação de sentimento baseada em léxico
            ├── influence.py   — ranking de influência determinístico (SHA-256)
            ├── trending.py    — trending topics ponderados
            ├── anomaly.py     — detecção de burst, alternância e sincronia
            ├── flags.py       — flags de funcionário MBRAS e padrão especial
            └── engine.py      — orquestra todos os componentes
"""

from analyzers.engine import analyze_feed

__all__ = ["analyze_feed"]
