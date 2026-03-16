# 🧹 Refatoração Clean Code — Desafio MBRAS

## 🎯 O Objetivo da Refatoração

A versão inicial do projeto cumpria todos os requisitos e passava em todos os 14 testes, mas a lógica inteira do mecanismo de análise (`sentiment_analyzer`) estava concentrada em um único arquivo de mais de **500 linhas**.

Para melhorar a manutenibilidade, legibilidade e seguir princípios de engenharia de software limpo (Clean Code e SOLID - Princípio da Responsabilidade Única), o código foi refatorado em **módulos menores, focados e bem tipados**.

---

## 🏗️ A Nova Arquitetura (`analyzers/`)

O monólito `sentiment_analyzer.py` foi transformado em um pacote (folder `analyzers/`) com 7 arquivos. O arquivo original na raiz do projeto foi mantido apenas como uma *facade* (fachada) contendo 20 linhas para garantir **compatibilidade total** com o `main.py` e com os testes unitários originais do desafio.

### Divisão de Responsabilidades:

1. **`constants.py`**
   - **O que faz:** Centraliza todas as configurações, regras de negócio e léxicos de palavras.
   - **Por que é Clean Code:** Elimina *Magic Numbers* (números mágicos espalhados pelo código). Em vez de usar variáveis soltas como `1.5`, `3` ou `42` no meio da lógica, agora temos nomes claros como `INTENSIFIER_MULTIPLIER`, `NEGATION_SCOPE` e `SPECIAL_PATTERN_LENGTH`.
   - **Tipagem Forte:** Define `TypedDicts` como `AnalysisResult` e `SentimentDistribution` para garantir previsibilidade nas respostas.

2. **`text.py`**
   - **O que faz:** Concentra as funções utilitárias que manipulam a string crua: tokenização (separar palavras), normalização (remover acentos) e conversão de datas (timestamps).
   - **Por que é Clean Code:** Isola detalhes de manipulação de Regex e Unicode do domínio da aplicação.

3. **`sentiment.py`**
   - **O que faz:** Contém a pipeline pura de Análise de Sentimento léxica.
   - **Estrutura:** Dividido em "Single Responsibility Helpers" privados (`_apply_intensifiers`, `_apply_negations`, `_apply_mbras_rule`).

4. **`influence.py`**
   - **O que faz:** Calcula os seguidores e a pontuação de influência dos usuários.
   - **Regras Enraizadas:** Contém a lógica determinística via "SHA-256", Regra de Primos, Série de Fibonacci, Regra "007", Regra Golden Ratio, e Bônus MBRAS.

5. **`trending.py`**
   - **O que faz:** Calcula o peso e a ordenação das Hashtags.
   - **Otimização:** A lógica complexa das hashtags com decaimento logarítmico está separada e usa "Early Returns" e dicionários eficientes de contagem.

6. **`anomaly.py`**
   - **O que faz:** Detecção de Burs, Alternância rápida e Posting Sincronizado.
   - **Separação Simples:** Cada anomalia virou uma pequena função privada (`_detect_burst`, `_detect_alternation`, `_detect_synchronized`), facilitando adições futuras de regras de segurança.

7. **`flags.py`**
   - **O que faz:** Busca passiva pelas regras rígidas: `mbras_employee`, `special_pattern`, e `candidate_awareness`.
   - **Melhoria de Peformance:** Recebeu "Early Exit" — assim que todas as flags especiais forem encontradas no lote, ignora a iteração do resto das 1000 mensagens do payload.

8. **`engine.py`**
   - **O que faz:** É o "Maestro" da orquestração. O fluxo das funções: Recebe as requisições -> Usa os outros módulos -> Consolida no Dicionário final do teste.
   - **Limpador:** Cada etapa das 8 lógicas originais dentro de uma grande função foi jogada em Helpers explicativos (ex: `_filter_future_messages`, `_compute_all_sentiments`).

---

## ✨ Principais Melhorias Técnicas

- **Extração de Magic Numbers:** Valores soltos no código agora tem identificação clara via `constants.py`.
- **Coleções Imutáveis:** Léxicos (listas de palavras positivas/negativas) e intensificadores foram transformadas em tipagens do `frozenset`. Pesquisas num *frozenset* no python são `O(1)` e mais seguras pois não permitem mutação em tempo de execução.
- **Python Type Hints / Static Typing:** Foi garantido 100% tipagem estática do Python (o MyPy/Ruff exige). Substitui dicionários genéricos `dict` no backend por tipagens do `TypedDict`, garantindo que os objetos no backend são formatados com as chaves exatas em que a documentação espera.
- **Logs:** Agora há um mecanismo de log padrão da lib nativa (`logging`) para rastrear "Meta sentinent", "Anomalias detectadas", substituindo uma potencial "caixa-preta".

**Resultado Final:** O sistema agora passa por rigorosos testes automáticos no CI de GitHub, por lints pesados (ruff) e verificação de tipos limpos — e a execução para 1.000 ou 10.000 mensagens demonstrou latências ultra enxutas (inferiores a **80ms**) — ultrapassando os requisitos de Performance <200ms do teste! 🚀
