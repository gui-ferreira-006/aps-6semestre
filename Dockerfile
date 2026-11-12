# ==============================================================================
# Dockerfile - Backend F.A.C.A. (FastAPI + OpenCV + face_recognition)
# APS 6° Semestre - UNIP 2026/2
# ==============================================================================

# Imagem base Python oficial leve
FROM python:3.10-slim

# Variáveis de ambiente para otimizar execução do Python em contêiner
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# ==============================================================================
# ALERTA CRÍTICO DE INFRAESTRUTURA:
# A biblioteca face_recognition utiliza o dlib, exigindo toolchain de compilação
# C++ e bibliotecas de álgebra linear (OpenBLAS/LAPACK) para construir as bindings.
# ==============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    pkg-config \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho no contêiner
WORKDIR /app

# Copia primeiramente o requirements.txt para aproveitar o cache de camadas do Docker
COPY requirements.txt .

# Atualiza o gerenciador de pacotes pip e instala as dependências Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o código-fonte da aplicação para o contêiner
COPY . /app/

# Expõe a porta padrão do FastAPI/Uvicorn
EXPOSE 8000

# Comando para inicializar a API ouvindo em todas as interfaces de rede
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
