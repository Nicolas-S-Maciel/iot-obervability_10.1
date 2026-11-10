# TechInova — Stack de Observabilidade (Indústria 4.0)

Projeto exemplo da disciplina **DevOps & Cloud Computing** — Módulo 7: Observabilidade
Prof. Nisflei Galoni

> Este projeto ** usa Docker **. Os containers são criados manualmente
> com `docker run`, usando rede, portas e volumes — conteúdos já estudados em
> *Docker: Network e Ports *.

## Cenário

A fábrica inteligente **TechInova** possui 3 linhas de produção (`Linha-A1`,
`Linha-B2`, `Linha-C3`). Cada linha tem sensores de **temperatura**, **vibração**
e **pressão**, além de contadores de **peças produzidas** e **falhas**.

```
  [ Sensores IoT ]          [ Coleta ]            [ Visualização ]
   iot-monitor:8000  ───►  prometheus:9090  ───►  grafana:3000
   (Python/FastAPI)        (time-series DB)       (dashboards)
        └──────────── rede docker: fabrica-net ────────────┘
```

## Como executar

Pré-requisito: Docker instalado e ativo.

### Opção A — Script auxiliar (mais rápido)

```bash
chmod +x subir.sh parar.sh
./subir.sh
```

### Opção B — Comandos manuais (recomendado para aprender)

```bash
# 1. Rede onde os 3 containers vão se comunicar pelo nome
docker network create fabrica-net

# 2. Constrói a imagem do microsserviço IoT
docker build -t iot-monitor ./app

# 3. Sobe o microsserviço IoT
docker run -d --name iot-monitor --network fabrica-net \
  -e UNIDADE_FABRIL=Sao-Bernardo \
  -p 8000:8000 iot-monitor

# 4. Sobe o Prometheus (monta os arquivos de configuração)
docker run -d --name prometheus --network fabrica-net \
  -p 9090:9090 \
  -v "$(pwd)/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml" \
  -v "$(pwd)/prometheus/alertas.yml:/etc/prometheus/alertas.yml" \
  prom/prometheus:v2.54.1

# 5. Sobe o Grafana (monta provisionamento e dashboard)
docker run -d --name grafana --network fabrica-net \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=techinova123 \
  -v "$(pwd)/grafana/provisioning:/etc/grafana/provisioning" \
  -v "$(pwd)/grafana/dashboards:/var/lib/grafana/dashboards" \
  grafana/grafana:11.2.0
```

> **Por que a rede importa?** O `prometheus.yml` aponta para o alvo
> `iot-monitor:8000` e o data source do Grafana aponta para `http://prometheus:9090`.
> Isso só resolve porque os três containers estão na mesma rede `fabrica-net`
> (resolução de nome por DNS interno do Docker).

Aguarde cerca de 30 segundos e acesse:

| Serviço            | URL                           | Credenciais            |
|--------------------|-------------------------------|------------------------|
| Microsserviço IoT  | http://localhost:8000         | —                      |
| Métricas brutas    | http://localhost:8000/metrics | —                      |
| Prometheus         | http://localhost:9090         | —                      |
| **Grafana**        | http://localhost:80         | `admin` / `techinova123` |

O dashboard **"TechInova - Chão de Fábrica"** já vem provisionado
automaticamente na pasta *Indústria 4.0* do Grafana.

> Em ambiente AWS (EC2), troque `localhost` pelo **IP público** da instância.

## Verificar e encerrar

```bash
docker ps                                   # os 3 containers devem aparecer
docker logs iot-monitor                     # logs do microsserviço

./parar.sh                                  # para e remove os containers
# ou manualmente:
docker rm -f iot-monitor prometheus grafana
docker network rm fabrica-net               # opcional: remove a rede
```

## Endpoints do microsserviço

| Endpoint   | Descrição                                            |
|------------|------------------------------------------------------|
| `/`        | Status do serviço                                    |
| `/health`  | Health check                                         |
| `/sensor`  | Leitura atual em JSON (consumo humano / SCADA)       |
| `/metrics` | Métricas no formato Prometheus (raspado a cada 5s)   |

## Métricas expostas

| Métrica                              | Tipo      | Significado                          |
|--------------------------------------|-----------|--------------------------------------|
| `techinova_temperatura_celsius`      | Gauge     | Temperatura do equipamento (°C)      |
| `techinova_vibracao_mm_s`            | Gauge     | Vibração do motor (mm/s RMS)         |
| `techinova_pressao_bar`              | Gauge     | Pressão da linha pneumática (bar)    |
| `techinova_maquina_operando`         | Gauge     | 1 = operando, 0 = parada             |
| `techinova_pecas_produzidas_total`   | Counter   | Total acumulado de peças             |
| `techinova_falhas_total`             | Counter   | Total de falhas por tipo             |
| `techinova_tempo_ciclo_segundos`     | Histogram | Distribuição do tempo de ciclo       |

## Estrutura

```
iot-observability/
├── subir.sh                    # sobe a stack (docker run)
├── parar.sh                    # para e remove os containers
├── app/
│   ├── main.py                 # microsserviço Python (sensores simulados)
│   ├── requirements.txt
│   └── Dockerfile
├── prometheus/
│   ├── prometheus.yml          # de onde coletar métricas
│   └── alertas.yml             # regras de alerta
└── grafana/
    ├── provisioning/           # conecta o Prometheus automaticamente
    └── dashboards/             # dashboard pré-construído
```

## Desafios (EAD)

1. Adicione um novo sensor de **umidade** ao `main.py`. Pare o container
   (`docker rm -f iot-monitor`), reconstrua a imagem
   (`docker build -t iot-monitor ./app`), suba novamente e crie um painel no Grafana.
2. Crie um alerta no Grafana que notifique quando a produção cair a zero.
3. Suba uma **segunda unidade fabril**: rode outro container com
   `docker run -d --name iot-campinas --network fabrica-net -e UNIDADE_FABRIL=Campinas -p 8001:8000 iot-monitor`,
   adicione esse alvo no `prometheus.yml` e compare as duas no dashboard
   usando a label `unidade`.
