import json
import random
import tracemalloc
import time
from datetime import datetime, timezone

from analyzers.engine import analyze_feed

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

def run_memory_test():
    print("Gerando payload de 10.000 mensagens...")
    messages = []
    for i in range(10000):
        content, tags = generate_random_content()
        messages.append({
            "id": f"msg_{i}",
            "content": content,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "user_id": f"user_{random.randint(1, 2000):04d}",
            "hashtags": tags,
            "reactions": random.randint(0, 50),
            "shares": random.randint(0, 15),
            "views": random.randint(100, 1000)
        })

    payload = {
        "messages": messages,
        "time_window_minutes": 60
    }
    
    print("\nIniciando medidor de memória (tracemalloc)...")
    tracemalloc.start()
    
    t0 = time.perf_counter()
    
    # Processa direto na engine (ignorando framework HTTP para testar a memória REAL do algoritmo)
    result = analyze_feed(payload)
    
    t1 = time.perf_counter()
    
    # Coleta a memória gasta
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    peak_mb = peak / (1024 * 1024)
    current_mb = current / (1024 * 1024)

    print(f"RESUMO MEMÓRIA | Pico: {peak_mb:.2f} MB | Tempo: {round((t1 - t0) * 1000, 2)} ms | Status: {'APROVADO' if peak_mb < 20 else 'REPROVADO'}")

if __name__ == "__main__":
    run_memory_test()
