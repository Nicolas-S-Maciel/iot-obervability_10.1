# ============================================================================
#  TechInova - Microsservico de Monitoramento IoT (Industria 4.0)
#  Disciplina: DevOps & Cloud Computing  |  Modulo 7 - Observabilidade
#  Prof. Nisflei Galoni
# ----------------------------------------------------------------------------
#  Este microsservico SIMULA os sensores de 3 linhas de producao de uma
#  fabrica inteligente. Ele expoe as leituras no endpoint /metrics no
#  formato Prometheus, para serem coletadas e visualizadas no Grafana.
# ============================================================================

import os
import random
import threading
import time

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# ----------------------------------------------------------------------------
# Identificacao da unidade fabril (vem de variavel de ambiente no container)
# ----------------------------------------------------------------------------
UNIDADE = os.environ.get("UNIDADE_FABRIL", "Sao-Bernardo")
LINHAS = ["Linha-A1", "Linha-B2", "Linha-C3"]

app = FastAPI(
    title="TechInova IoT Monitor",
    description="Microsservico de telemetria das linhas de producao - Industria 4.0",
    version="1.0.0",
)

# ----------------------------------------------------------------------------
# DEFINICAO DAS METRICAS PROMETHEUS
# ----------------------------------------------------------------------------
# Gauge  -> valor que sobe e desce (temperatura, vibracao, pressao)
# Counter-> valor que so cresce (total de pecas, total de falhas)
# Histogram -> distribuicao de valores (tempo de ciclo da maquina)
# ----------------------------------------------------------------------------

sensor_temperatura = Gauge(
    "techinova_temperatura_celsius",
    "Temperatura do equipamento em graus Celsius",
    ["unidade", "linha"],
)

sensor_vibracao = Gauge(
    "techinova_vibracao_mm_s",
    "Vibracao do motor em mm/s (RMS)",
    ["unidade", "linha"],
)

sensor_pressao = Gauge(
    "techinova_pressao_bar",
    "Pressao da linha pneumatica em bar",
    ["unidade", "linha"],
)

pecas_produzidas = Counter(
    "techinova_pecas_produzidas_total",
    "Total acumulado de pecas produzidas",
    ["unidade", "linha"],
)

falhas_total = Counter(
    "techinova_falhas_total",
    "Total acumulado de falhas detectadas nos sensores",
    ["unidade", "linha", "tipo"],
)

maquina_status = Gauge(
    "techinova_maquina_operando",
    "Status da maquina: 1=operando, 0=parada",
    ["unidade", "linha"],
)

tempo_ciclo = Histogram(
    "techinova_tempo_ciclo_segundos",
    "Tempo de ciclo de producao por peca (segundos)",
    ["unidade", "linha"],
    buckets=(1, 2, 3, 5, 8, 13, 21),
)

requisicoes_http = Counter(
    "techinova_http_requests_total",
    "Total de requisicoes HTTP recebidas pelo microsservico",
    ["endpoint"],
)


# ----------------------------------------------------------------------------
# THREAD DE SIMULACAO
# Em uma fabrica real, esses valores viriam de CLPs / sensores via MQTT,
# OPC-UA ou Modbus. Aqui geramos dados realistas para o laboratorio.
# ----------------------------------------------------------------------------
def simular_chao_de_fabrica() -> None:
    # Estado base de cada linha
    estado = {
        linha: {
            "temp": random.uniform(60, 70),
            "vib": random.uniform(1.5, 3.0),
            "press": random.uniform(5.5, 6.5),
            "operando": True,
        }
        for linha in LINHAS
    }

    while True:
        for linha in LINHAS:
            s = estado[linha]

            # 2% de chance da maquina parar; 10% de voltar a operar se parada
            if s["operando"] and random.random() < 0.02:
                s["operando"] = False
            elif not s["operando"] and random.random() < 0.10:
                s["operando"] = True

            maquina_status.labels(UNIDADE, linha).set(1 if s["operando"] else 0)

            if not s["operando"]:
                # Maquina parada: temperatura cai, sem producao
                s["temp"] = max(25, s["temp"] - random.uniform(0.5, 1.5))
                sensor_temperatura.labels(UNIDADE, linha).set(round(s["temp"], 2))
                sensor_vibracao.labels(UNIDADE, linha).set(0)
                sensor_pressao.labels(UNIDADE, linha).set(0)
                time.sleep(0.05)
                continue

            # Variacao suave (random walk) das grandezas fisicas
            s["temp"] += random.uniform(-0.8, 1.0)
            s["vib"] += random.uniform(-0.3, 0.35)
            s["press"] += random.uniform(-0.2, 0.2)

            # Limites fisicos
            s["temp"] = min(max(s["temp"], 40), 105)
            s["vib"] = min(max(s["vib"], 0.5), 9.0)
            s["press"] = min(max(s["press"], 3.0), 8.5)

            sensor_temperatura.labels(UNIDADE, linha).set(round(s["temp"], 2))
            sensor_vibracao.labels(UNIDADE, linha).set(round(s["vib"], 2))
            sensor_pressao.labels(UNIDADE, linha).set(round(s["press"], 2))

            # Producao: cada ciclo gera de 1 a 3 pecas
            qtd = random.randint(1, 3)
            pecas_produzidas.labels(UNIDADE, linha).inc(qtd)
            tempo_ciclo.labels(UNIDADE, linha).observe(random.uniform(1.5, 12))

            # Deteccao de falhas com base em limites de seguranca
            if s["temp"] > 90:
                falhas_total.labels(UNIDADE, linha, "superaquecimento").inc()
            if s["vib"] > 7:
                falhas_total.labels(UNIDADE, linha, "vibracao_excessiva").inc()
            if s["press"] < 4:
                falhas_total.labels(UNIDADE, linha, "baixa_pressao").inc()

        # Intervalo entre leituras (a cada 2s, como um sensor real)
        time.sleep(2)


# ----------------------------------------------------------------------------
# ENDPOINTS HTTP
# ----------------------------------------------------------------------------
@app.get("/")
def status():
    requisicoes_http.labels("/").inc()
    return {
        "servico": "TechInova IoT Monitor",
        "unidade": UNIDADE,
        "linhas": LINHAS,
        "status": "online",
        "aluno": "<Coloque seu nome>",
        "dica": "Metricas disponiveis em /metrics",
    }


@app.get("/health")
def health():
    requisicoes_http.labels("/health").inc()
    return JSONResponse({"status": "ok"})


@app.get("/sensor")
def leitura_atual():
    """Snapshot legivel das ultimas leituras (uso humano / SCADA)."""
    requisicoes_http.labels("/sensor").inc()
    leituras = []
    for linha in LINHAS:
        leituras.append(
            {
                "linha": linha,
                "temperatura_celsius": sensor_temperatura.labels(UNIDADE, linha)._value.get(),
                "vibracao_mm_s": sensor_vibracao.labels(UNIDADE, linha)._value.get(),
                "pressao_bar": sensor_pressao.labels(UNIDADE, linha)._value.get(),
                "operando": bool(maquina_status.labels(UNIDADE, linha)._value.get()),
            }
        )
    return {"unidade": UNIDADE, "leituras": leituras}


@app.get("/metrics")
def metrics():
    """Endpoint raspado pelo Prometheus a cada 5s."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ----------------------------------------------------------------------------
# Inicia a simulacao em background quando o app sobe
# ----------------------------------------------------------------------------
@app.on_event("startup")
def iniciar_simulacao():
    t = threading.Thread(target=simular_chao_de_fabrica, daemon=True)
    t.start()
