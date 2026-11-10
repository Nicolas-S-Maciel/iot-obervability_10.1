#!/usr/bin/env bash
set -e

# Pasta onde este script esta (raiz do projeto)
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ">> 1/5  Criando a rede fabrica-net..."
docker network create fabrica-net 2>/dev/null || echo "   (rede ja existe, ok)"

echo ">> 2/5  Construindo a imagem do microsservico IoT..."
docker build -t iot-monitor ./app

echo ">> 3/5  Subindo o microsservico IoT (porta 8000)..."
docker rm -f iot-monitor 2>/dev/null || true
docker run -d --name iot-monitor --network fabrica-net \
  -e UNIDADE_FABRIL=Sao-Bernardo \
  -p 8000:8000 iot-monitor

echo ">> 4/5  Subindo o Prometheus (porta 9090)..."
docker rm -f prometheus 2>/dev/null || true
docker run -d --name prometheus --network fabrica-net \
  -p 9090:9090 \
  -v "$DIR/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml" \
  -v "$DIR/prometheus/alertas.yml:/etc/prometheus/alertas.yml" \
  prom/prometheus:v2.54.1

echo ">> 5/5  Subindo o Grafana (porta 3000)..."
docker rm -f grafana 2>/dev/null || true
docker run -d --name grafana --network fabrica-net \
  -p 80:3000 \
  -e GF_SECURITY_ADMIN_USER=admin \
  -e GF_SECURITY_ADMIN_PASSWORD=techinova123 \
  -v "$DIR/grafana/provisioning:/etc/grafana/provisioning" \
  -v "$DIR/grafana/dashboards:/var/lib/grafana/dashboards" \
  grafana/grafana:11.2.0

echo ""
echo "OK! Aguarde ~30s e acesse:"
echo "  - Microsservico IoT : http://localhost:8000"
echo "  - Prometheus        : http://localhost:9090"
echo "  - Grafana           : http://localhost:80  (admin / techinova123)"
echo "  (em EC2, troque localhost pelo IP publico da instancia)"
