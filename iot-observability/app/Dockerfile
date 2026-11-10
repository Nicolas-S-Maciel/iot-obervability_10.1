# ============================================================
#  TechInova - Microsservico de Monitoramento IoT
#  Imagem Docker do servico de telemetria (Industria 4.0)
# ============================================================

# Imagem base leve - ideal para microsservicos
FROM python:3.11-slim

# Diretorio de trabalho dentro do container
WORKDIR /app

# Copia e instala as dependencias primeiro (aproveita cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo da aplicacao
COPY main.py .

# Variavel de ambiente: nome da unidade fabril (pode ser sobrescrita)
ENV UNIDADE_FABRIL=Sao-Bernardo

# Porta do microsservico
EXPOSE 8000

# Sobe o servidor ASGI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
