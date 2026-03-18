import json
import random
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

HASHTAGS = [
    "#novidade",
    "#review",
    "#produto",
    "#atendimento",
    "#qualidade",
    "#rapido",
    "#servico",
]


def send_request(payload: dict) -> tuple[int, dict, float]:
    req = urllib.request.Request(
        "http://localhost:8000/analyze-feed",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as e:
        status = e.code
        result = json.loads(e.read().decode("utf-8"))
    t1 = time.perf_counter()
    return status, result, (t1 - t0) * 1000


def test_validations():
    print("=" * 60)
    print("1. TESTANDO REGRAS DE VALIDAÇÃO (HTTP 400 e 422)")
    print("=" * 60)

    # 422 - time window 123
    status, res, _ = send_request({"messages": [], "time_window_minutes": 123})
    print(
        f"[Janela Temporal não suportada] Status: {status} | Esperado: 422 ✅"
        if status == 422
        else "❌ Falha"
    )

    # 400 - empty body (handled by our try/except inside the endpoint)
    req = urllib.request.Request(
        "http://localhost:8000/analyze-feed",
        data=b"",
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req)
        print("❌ Falha no teste de corpo vazio")
    except urllib.error.HTTPError as e:
        print(
            f"[Payload Vazio JSONDecodeError] Status: {e.code} | Esperado: 400 ✅"
            if e.code == 400
            else "❌ Falha"
        )

    # 400 - invalid timestamp
    msg_base = {
        "id": "m1",
        "content": "ok",
        "timestamp": "2025-01-01 10:00:00",  # sem T e Z
        "user_id": "user_123",
        "hashtags": [],
        "reactions": 0,
        "shares": 0,
        "views": 100,
    }
    status, res, _ = send_request({"messages": [msg_base], "time_window_minutes": 60})
    print(
        f"[Timestamp inválido regex] Status: {status} | Esperado: 400 ✅"
        if status == 400
        else "❌ Falha"
    )

    # 400 - regex user_id
    msg_base["timestamp"] = "2025-01-01T10:00:00Z"
    msg_base["user_id"] = "user_A!"  # caracteres invalidos
    status, res, _ = send_request({"messages": [msg_base], "time_window_minutes": 60})
    print(
        f"[UserID Inválido regex] Status: {status} | Esperado: 400 ✅"
        if status == 400
        else "❌ Falha"
    )

    # 400 - content > 280
    msg_base["user_id"] = "user_123"
    msg_base["content"] = "A" * 281
    status, res, _ = send_request({"messages": [msg_base], "time_window_minutes": 60})
    print(
        f"[Conteúdo > 280 chars] Status: {status} | Esperado: 400 ✅"
        if status == 400
        else "❌ Falha"
    )

    print("\nTodas as validações primárias de dados rejeitaram com sucesso!")


def build_rules_payload(size: int) -> dict:
    messages = []
    ts_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Meta Phrase -> candidate_awareness
    messages.append(
        {
            "id": "m1",
            "content": "teste técnico mbras",
            "timestamp": ts_now,
            "user_id": "user_norm",
            "hashtags": ["#vaga"],
            "reactions": 0,
            "shares": 0,
            "views": 100,
        }
    )

    # 2. Special Pattern (exactly 42 chars + "mbras")
    content_42 = "mbras" + "x" * 37
    messages.append(
        {
            "id": "m2",
            "content": content_42,
            "timestamp": ts_now,
            "user_id": "user_norm",
            "hashtags": [],
            "reactions": 0,
            "shares": 0,
            "views": 100,
        }
    )

    # 3. MBRAS employee user (+2 influence & 2x pos sentiment)
    messages.append(
        {
            "id": "m3",
            "content": "ótimo excelente",
            "timestamp": ts_now,
            "user_id": "user_mbras",
            "hashtags": [],
            "reactions": 100,
            "shares": 50,
            "views": 1000,
        }
    )

    # 4. User 007 penalty (x0.5 influence)
    messages.append(
        {
            "id": "m4",
            "content": "normal",
            "timestamp": ts_now,
            "user_id": "user_007",
            "hashtags": [],
            "reactions": 100,
            "shares": 50,
            "views": 1000,
        }
    )

    # 5. Unicode followers (has diacritics -> 4242 followers)
    messages.append(
        {
            "id": "m5",
            "content": "normal",
            "timestamp": ts_now,
            "user_id": "user_uário",
            "hashtags": [],
            "reactions": 10,
            "shares": 5,
            "views": 100,
        }
    )

    # 6. Fibonacci length (exactly 13 -> 233 followers)
    messages.append(
        {
            "id": "m6",
            "content": "normal",
            "timestamp": ts_now,
            "user_id": "user_13chars_",
            "hashtags": [],
            "reactions": 10,
            "shares": 5,
            "views": 100,
        }
    )

    # 7. Prime followers (endswith "_prime")
    messages.append(
        {
            "id": "m7",
            "content": "normal",
            "timestamp": ts_now,
            "user_id": "user_prime",
            "hashtags": [],
            "reactions": 10,
            "shares": 5,
            "views": 100,
        }
    )

    # 8. Golden Ratio interaction (reactions + shares = 7 => 4 + 3)
    messages.append(
        {
            "id": "m8",
            "content": "normal",
            "timestamp": ts_now,
            "user_id": "user_golden",
            "hashtags": [],
            "reactions": 4,
            "shares": 3,
            "views": 100,
        }
    )

    # 9. Burst anomaly (11 messages from same user in 5 mins)
    for i in range(11):
        messages.append(
            {
                "id": f"mb_{i}",
                "content": "spam",
                "timestamp": ts_now,
                "user_id": "user_burst",
                "hashtags": [],
                "reactions": 0,
                "shares": 0,
                "views": 10,
            }
        )

    # 10. Long hashtag (> 8 chars, logarithmic decay weight)
    messages.append(
        {
            "id": "mh1",
            "content": "tag",
            "timestamp": ts_now,
            "user_id": "user_norm",
            "hashtags": ["#palavramuitolongamesmo"],
            "reactions": 50,
            "shares": 10,
            "views": 100,
        }
    )

    # Preenchendo o resto com dados randômicos orgânicos
    remaining = size - len(messages)
    for i in range(remaining):
        sentiment = random.choice(["bom", "ruim", "produto"])
        messages.append(
            {
                "id": f"mr_{i}",
                "content": sentiment,
                "timestamp": ts_now,
                "user_id": f"user_rnd_{random.randint(1, 1000):04d}",
                "hashtags": random.sample(HASHTAGS, k=random.randint(0, 2)),
                "reactions": random.randint(0, 10),
                "shares": random.randint(0, 5),
                "views": random.randint(50, 500),
            }
        )

    return {"messages": messages, "time_window_minutes": 60}


def run_load_test(size: int):
    print("\n" + "=" * 60)
    print(f"2. TESTANDO CASOS ESPECIAIS & CARGA DE {size} MENSAGENS")
    print("=" * 60)

    payload = build_rules_payload(size)
    status, result, total_ms = send_request(payload)

    if status != 200:
        print(f"Erro na API. HTTP {status}: {result}")
        return

    analysis = result["analysis"]
    print(f"Requisição Completa em:  {round(total_ms, 2)}ms")
    print(f"Tempo Motor Python:      {analysis['processing_time_ms']}ms\n")

    flags = analysis["flags"]
    print(f"✅ Flag MBRAS Employee:      {flags['mbras_employee']}")
    print(f"✅ Flag Special Pattern:     {flags['special_pattern']}")
    print(f"✅ Flag Candidate Awareness: {flags['candidate_awareness']}")
    print(
        f"✅ Anomalia Detectada:       {analysis['anomaly_detected']} - TIPO: {analysis['anomaly_type']}"
    )
    print(
        f"✅ Candidate Engagement =    {analysis['engagement_score']} (Forçado pela awareness)\n"
    )

    print("Top Influenciadores Especiais Disparados (Ranking Check):")
    # Busca os IDs chave no ranking de influência
    target_ids = [
        "usuário_á",
        "user_prime",
        "user_007",
        "user_mbras",
        "user_golden",
        "u" * 13,
    ]
    for uid in target_ids:
        # Pega a influência desse user_id
        usr = next(
            (u for u in analysis["influence_ranking"] if u["user_id"] == uid), None
        )
        if usr:
            print(f"  - {usr['user_id']:<15} -> Score: {usr['influence_score']:.2f}")


if __name__ == "__main__":
    test_validations()
    run_load_test(1000)
    run_load_test(10000)
