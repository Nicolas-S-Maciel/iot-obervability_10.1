#!/usr/bin/env bash

echo ">> Parando e removendo os containers..."
docker rm -f iot-monitor prometheus grafana 2>/dev/null || true

docker network rm fabrica-net 2>/dev/null || true

echo "OK! Containers e redes removidos."
