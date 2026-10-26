FROM python:3.11-slim

# Evita arquivos .pyc, bufferiza logs e garante codificação UTF-8 padrão
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1

WORKDIR /app

# Instala curl (necessário para healthcheck) e ferramentas básicas de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python primeiro (aproveita cache de camadas)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte, dicionários e assets
COPY . .

# Expõe as portas de serviço:
# - 8000: Microserviço REST isolado (api_anonimizador.py)
# - 7860: Aplicação completa com interfaces gráficas (app.py)
EXPOSE 8000 7860

# Comando padrão: inicia a API isolada
CMD ["python", "api_anonimizador.py"]
