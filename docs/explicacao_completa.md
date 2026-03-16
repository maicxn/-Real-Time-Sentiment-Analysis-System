# 📖 Explicação Completa — Desafio MBRAS

## 📋 O Que o Teste Pede

O desafio pede a criação de um **Sistema de Análise de Sentimentos em Tempo Real** que:

1. Recebe um **feed de mensagens** via API REST (`POST /analyze-feed`)
2. Analisa o sentimento de cada mensagem (positivo, negativo, neutro)
3. Calcula métricas de engajamento e influência dos usuários
4. Detecta trending topics (hashtags mais populares)
5. Detecta anomalias no comportamento dos usuários
6. Aplica regras especiais para funcionários MBRAS

### O que é avaliado

| Critério | Peso | O que significa |
|----------|------|-----------------|
| Algoritmos | 50% | Implementação correta e determinística (mesmo input = mesmo output) |
| Performance | 30% | < 200ms para 1000 mensagens, uso eficiente de memória |
| Qualidade | 20% | Código organizado, legível, com tratamento de erros |

### Os 6 Casos de Teste Obrigatórios

| Teste | O que valida |
|-------|-------------|
| **1 — Básico** | Sentimento positivo detectado para "Adorei o produto!", hashtag `#produto` aparece nos trending topics |
| **2A — Erro 422** | `time_window_minutes = 123` retorna HTTP 422 com código `UNSUPPORTED_TIME_WINDOW` |
| **2B — Flags Especiais** | `mbras_employee = true`, `candidate_awareness = true`, `engagement_score = 9.42` |
| **3A — Intensificador Órfão** | "muito" sozinho = 100% neutro (intensificador sem palavra de sentimento para amplificar) |
| **3B — Negação Dupla** | "não não gostei" = positivo (duas negações se cancelam) |
| **3C — Case Sensitivity** | `user_MBRAS_007` → `mbras_employee = true` (case-insensitive) |

Além desses 6, existem mais 8 testes extras (totalizando **14 testes** no arquivo `test_analyzer.py`).

---

## 🏗️ Estrutura dos Arquivos Criados

```
├── main.py                  # Servidor FastAPI (endpoint + validação)
├── sentiment_analyzer.py    # Lógica pura de análise (todas as funções)
├── requirements.txt         # Dependências do Python
├── .github/workflows/ci.yml # Pipeline CI com 3 etapas
```

---

## 🔧 O Que Cada Arquivo Faz

### `main.py` — Servidor FastAPI

Este arquivo é o **ponto de entrada** da aplicação. Ele:

1. **Cria o servidor FastAPI** e expõe o endpoint `POST /analyze-feed`
2. **Valida os dados de entrada** (validação de input → erro 400)
3. **Aplica regras de negócio** (ex: janela temporal 123 → erro 422)
4. **Chama a função pura** `analyze_feed()` do módulo de análise
5. **Retorna o resultado** encapsulado em `{"analysis": {...}}`

#### Validações Implementadas (retornam HTTP 400)

| Campo | Regra |
|-------|-------|
| `user_id` | Deve seguir o padrão `user_[caracteres]{3+}` (regex com Unicode) |
| `content` | Máximo 280 caracteres Unicode |
| `timestamp` | Formato RFC 3339 com sufixo `Z` obrigatório (ex: `2025-09-10T10:00:00Z`) |
| `hashtags` | Array de strings, cada uma começando com `#` |
| `time_window_minutes` | Deve ser > 0 |

#### Regra de Negócio (retorna HTTP 422)

- Se `time_window_minutes == 123` → retorna `{"error": "Valor de janela temporal não suportado na versão atual", "code": "UNSUPPORTED_TIME_WINDOW"}`

---

### `sentiment_analyzer.py` — Motor de Análise

Este é o **coração do sistema**. Contém toda a lógica de análise como funções puras (determinísticas). Abaixo está cada função explicada em detalhe.

---

## 🔍 Explicação de Cada Função

### Funções Auxiliares de Texto

#### `_normalize_nfkd(text: str) -> str`

**O que faz:** Normaliza texto para comparação com o léxico.

**Passos:**
1. Converte para minúsculas (`"Adorei"` → `"adorei"`)
2. Aplica normalização NFKD (decompõe caracteres acentuados)
3. Remove marcas diacríticas (acentos)

**Por quê:** Para que "ótimo" e "otimo" correspondam à mesma palavra no léxico. A normalização NFKD decompõe `ó` em `o` + acento agudo, e depois removemos o acento.

**Exemplo:**
```
"Adorei" → "adorei"     (só lowercase)
"ótimo"  → "otimo"      (remove acento)
"café"   → "cafe"       (remove acento)
```

---

#### `_tokenize(content: str) -> list[str]`

**O que faz:** Divide o texto em tokens (palavras e hashtags).

**Regex usada:** `r'(?:#\w+(?:-\w+)*)|\b\w+\b'` com flag Unicode.

**Regras:**
- Hashtags compostas como `#produto-novo` são mantidas como um único token
- Pontuação é removida (`!`, `?`, etc.)
- Cada palavra é um token separado

**Exemplos:**
```
"Adorei o produto!"           → ["Adorei", "o", "produto"]
"Não muito bom! #produto"    → ["Não", "muito", "bom", "#produto"]
"#produto-novo ótimo!"       → ["#produto-novo", "ótimo"]
```

---

#### `_has_diacritics(text: str) -> bool`

**O que faz:** Verifica se o texto contém acentos/diacríticos.

**Usada para:** Caso especial onde `user_id` com acentos (ex: `user_café`) recebe `followers = 4242`.

---

### Análise de Sentimento

#### `_compute_sentiment(content: str, is_mbras: bool) -> tuple[float, str]`

**O que faz:** Calcula o sentimento de uma única mensagem.

**Retorna:** `(score numérico, classificação)` onde classificação é `"positive"`, `"negative"`, `"neutral"` ou `"meta"`.

**Pipeline (ordem fixa e obrigatória):**

```
1. Verificar meta-sentimento ("teste técnico mbras")
2. Tokenizar o texto
3. Normalizar tokens para comparação com léxico
4. Identificar palavras positivas/negativas no léxico
5. Aplicar intensificadores (×1.5)
6. Aplicar negações (escopo 3 tokens, paridade)
7. Aplicar regra MBRAS (×2 positivos)
8. Calcular score = soma / quantidade de tokens
9. Classificar: >0.1 = positive, <-0.1 = negative, senão = neutral
```

**O léxico contém:**

| Tipo | Palavras |
|------|----------|
| **Positivas** (+1) | adorei, gostei, excelente, ótimo, perfeito, bom, maravilhoso, incrível, fantástico, sensacional, top |
| **Negativas** (-1) | ruim, terrível, péssimo, horrível, odiei, detestei, nojento, decepcionante |
| **Intensificadores** (×1.5) | muito, super, extremamente, bastante, demais, incrivelmente, absurdamente |
| **Negações** (inverte) | não, nunca, jamais, nem, tampouco |

**Exemplos detalhados:**

```
Exemplo 1: "Adorei o produto!" (usuário normal)
  Tokens:  ["Adorei", "o", "produto"]
  Scores:  [+1.0,    0.0,  0.0]  → adorei = positivo
  Total:   1.0 / 3 = 0.333 → > 0.1 → "positive"

Exemplo 2: "muito" (intensificador órfão)
  Tokens:  ["muito"]
  Scores:  [0.0]  → muito é intensificador, não tem polaridade própria
  Total:   0.0 / 1 = 0.0 → [-0.1, 0.1] → "neutral"

Exemplo 3: "não não gostei" (negação dupla)
  Tokens:  ["não", "não", "gostei"]
  Scores:  [0.0,   0.0,   +1.0]  → gostei = positivo
  Negação: "gostei" recebe 2 negações → paridade par → cancela!
  Total:   1.0 / 3 = 0.333 → "positive"

Exemplo 4: "Não muito bom" (intensificador + negação)
  Tokens:  ["Não", "muito", "bom"]
  Scores:  [0.0,   0.0,    +1.0]
  Step 1 - Intensificador: muito amplifica bom → +1.5
  Step 2 - Negação: não inverte bom → -1.5
  Total: -1.5 / 3 = -0.5 → "negative"

Exemplo 5: "Super adorei!" (user_mbras_123 → MBRAS)
  Tokens:  ["Super", "adorei"]
  Scores:  [0.0,    +1.0]
  Step 1 - Intensificador: super amplifica adorei → +1.5
  Step 3 - MBRAS: positivo × 2 → +3.0
  Total: 3.0 / 2 = 1.5 → "positive"
```

---

### Influência de Usuários

#### `_compute_followers(user_id: str) -> int`

**O que faz:** Calcula seguidores simulados de forma **determinística** (mesmo user_id = sempre mesmo resultado).

**Lógica com casos especiais:**

```
1. Se user_id tem acentos (ex: user_café) → followers = 4242
2. Se user_id tem exatamente 13 caracteres → followers = 233 (13º Fibonacci)
3. Se user_id termina com "_prime" → followers = soma dos primeiros N primos (N = tamanho do user_id)
4. Caso padrão → SHA-256 determinístico:
   followers = (int(sha256(user_id), 16) % 10000) + 100
   Resultado: entre 100 e 10099
```

---

#### `_first_n_primes(n: int) -> list[int]`

**O que faz:** Retorna os primeiros N números primos. Usado pelo caso especial `_prime`.

---

#### `_compute_influence(user_id, reactions, shares, views, is_mbras) -> float`

**O que faz:** Calcula o score de influência de um usuário.

**Fórmula:**
```
1. followers = _compute_followers(user_id)
2. engagement_rate = (reactions + shares) / max(views, 1)
3. Se (reactions + shares) é múltiplo de 7 → rate × (1 + 1/φ)  [Golden Ratio]
4. score = (followers × 0.4) + (engagement_rate × 0.6)
5. Se user_id termina em "007" → score × 0.5  [penalidade]
6. Se é funcionário MBRAS → score + 2.0  [bônus]
```

---

### Trending Topics

#### `_compute_trending(messages, sentiments, now_utc) -> list[str]`

**O que faz:** Retorna as **top 5 hashtags** ordenadas por peso.

**Cálculo do peso de cada hashtag:**
```
peso = peso_temporal × modificador_sentimento × fator_hashtag_longa
```

**Componentes:**
- **Peso temporal:** `1 + (1 / minutos_desde_postagem)` — mais recente = mais peso
- **Modificador de sentimento:** positivo ×1.2, negativo ×0.8, neutro ×1.0
- **Fator de hashtag longa:** se > 8 caracteres, aplica `log₁₀(tamanho) / log₁₀(8)`

**Desempate (em ordem):**
1. Maior peso total
2. Maior frequência (contagem)
3. Maior peso de sentimento
4. Ordem lexicográfica (alfabética)

---

### Detecção de Anomalias

#### `_detect_anomalies(messages, sentiments) -> tuple[bool, str | None]`

**O que faz:** Detecta 3 tipos de comportamento anômalo:

| Anomalia | Regra |
|----------|-------|
| **Burst** | Mais de 10 mensagens do mesmo usuário em 5 minutos |
| **Alternation** | Padrão exato positivo-negativo-positivo-negativo em ≥ 10 mensagens do mesmo usuário |
| **Synchronized Posting** | 3 ou mais mensagens com timestamps dentro de ±2 segundos |

---

### Flags Especiais

#### `_compute_flags(messages) -> dict`

**O que faz:** Verifica flags especiais no conjunto de mensagens.

| Flag | Condição |
|------|----------|
| `mbras_employee` | `user_id` contém "mbras" (case-insensitive). Ex: `user_MBRAS_007` ✅ |
| `special_pattern` | `content` tem exatamente 42 caracteres Unicode E contém "mbras" |
| `candidate_awareness` | `content` contém a frase "teste técnico mbras" |

---

### Função Principal

#### `analyze_feed(data: dict) -> dict`

**O que faz:** Orquestra toda a análise. É a **função pura** chamada pelo endpoint.

**Fluxo completo:**

```
1. Receber mensagens e time_window
2. Filtrar mensagens futuras (tolerância de 5s)
3. Calcular flags (mbras_employee, special_pattern, candidate_awareness)
4. Para cada mensagem:
   a. Verificar se o usuário é MBRAS
   b. Calcular sentimento (positivo/negativo/neutro/meta)
5. Calcular distribuição de sentimento (% positivo/negativo/neutro)
   → Mensagens "meta" são excluídas da distribuição
6. Calcular engagement_score:
   → Se candidate_awareness = true → 9.42 (valor fixo)
   → Senão → (reactions + shares) / views
7. Calcular ranking de influência por usuário
8. Calcular trending topics (top 5 hashtags)
9. Detectar anomalias
10. Retornar resultado completo com processing_time_ms
```

**Estrutura da resposta:**
```json
{
  "analysis": {
    "sentiment_distribution": {"positive": 100.0, "negative": 0.0, "neutral": 0.0},
    "engagement_score": 0.12,
    "trending_topics": ["#produto", "#review"],
    "influence_ranking": [{"user_id": "user_123", "influence_score": 1234.5}],
    "anomaly_detected": false,
    "anomaly_type": null,
    "flags": {"mbras_employee": false, "special_pattern": false, "candidate_awareness": false},
    "processing_time_ms": 1.23
  }
}
```

---

## 🔄 CI/CD — Pipeline de Integração Contínua

O arquivo `.github/workflows/ci.yml` configura **3 etapas** no GitHub Actions:

| Etapa | Ferramenta | O que faz |
|-------|-----------|-----------|
| **Lint** | `ruff` | Verifica qualidade do código e formatação |
| **Test** | `pytest` | Roda todos os 14 testes unitários + teste de performance |
| **Type Check** | `mypy` | Verifica tipos estáticos (segurança de tipagem) |

A etapa de **Test** depende do **Lint** passar primeiro. O **Type Check** também roda em paralelo após o lint.

---

## ⚡ Medidas de Performance

- **Algoritmos O(n):** Processamento é linear no número de mensagens
- **Sem dependências pesadas:** Apenas stdlib do Python + FastAPI
- **Resultado:** < 200ms para 1000 mensagens (meta atingida ✅)
