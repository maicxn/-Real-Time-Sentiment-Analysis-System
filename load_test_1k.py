import json
import random
import time
import urllib.request
from datetime import datetime, timezone

# Listas extraídas das constantes oficiais para gerar mocks variados
POSITIVE_WORDS = ["adorei", "gostei", "excelente", "otimo", "perfeito", "bom", "maravilhoso", "incrivel", "fantastico"]
NEGATIVE_WORDS = ["ruim", "terrivel", "pessimo", "horrivel", "odiei", "detestei", "decepcionante"]
NEUTRAL_WORDS = ["produto", "chegou", "ontem", "hoje", "normal", "ok", "mensagem", "teste"]
INTENSIFIERS = ["muito ", "super ", "extremamente ", ""]
HASHTAGS = ["#novidade", "#review", "#produto", "#atendimento", "#qualidade", "#rapido", "#servico"]

def generate_random_content() -> tuple[str, list[str]]:
    sentiment_type = random.choices(["pos", "neg", "neu", "meta"], weights=[40, 30, 20, 10])[0]
    
    if sentiment_type == "meta":
        return "este é um teste técnico mbras maravilhoso", ["#vaga"]
        
    intensifier = random.choice(INTENSIFIERS)
    subject = random.choice(NEUTRAL_WORDS)
    
    if sentiment_type == "pos":
        word = random.choice(POSITIVE_WORDS)
        content = f"O {subject} é {intensifier}{word}!"
    elif sentiment_type == "neg":
        word = random.choice(NEGATIVE_WORDS)
        content = f"Sinceramente, achei o {subject} {intensifier}{word}."
    else:
        content = f"Apenas um comentário {subject} sobre o sistema."
        
    tags = random.sample(HASHTAGS, k=random.randint(0, 3))
    return content, tags

def run_1k_test():
    print("Gerando 1000 mensagens com variância orgânica de sentimentos...")
    
    messages = []
    for i in range(1000):
        content, tags = generate_random_content()
        messages.append({
            "id": f"msg_{i}",
            "content": content,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user_id": f"user_{random.randint(1, 200):04d}", # Força repetição p/ criar anomalies/influencers
            "hashtags": tags,
            "reactions": random.randint(0, 50),
            "shares": random.randint(0, 15),
            "views": random.randint(100, 1000)
        })

    payload = json.dumps({
        "messages": messages,
        "time_window_minutes": 60
    }).encode("utf-8")

    req = urllib.request.Request(
        "http://localhost:8000/analyze-feed",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    print("Enviando requisição POST para http://localhost:8000/analyze-feed ...")
    
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as e:
        status = e.code
        result = json.loads(e.read().decode("utf-8"))
        
    t1 = time.perf_counter()

    print("\n" + "="*50)
    print(f"Status HTTP:       {status}")
    print(f"Tempo da Call:     {round((t1 - t0) * 1000, 2)}ms")
    if "analysis" in result:
        print(f"Processing time:   {result['analysis']['processing_time_ms']}ms")
    print("="*50 + "\n")
    
    if "analysis" in result:
        a = result["analysis"]
        print("Sentimento:")
        print(f"  Positivo:  {a['sentiment_distribution']['positive']}%")
        print(f"  Negativo:  {a['sentiment_distribution']['negative']}%")
        print(f"  Neutro:    {a['sentiment_distribution']['neutral']}%")
        print(f"\nEngagement score:  {a['engagement_score']}")
        print(f"Trending topics:   {a['trending_topics']}")
        print(f"Anomalia:          {a['anomaly_detected']} ({a['anomaly_type']})")
        
        print("\nTop 5 influência:")
        for u in a['influence_ranking'][:5]:
            print(f"  {u['user_id']:<30} score={u['influence_score']}")
    else:
        print("Erro:", result)

if __name__ == "__main__":
    run_1k_test()
