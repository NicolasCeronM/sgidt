# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Paquetes de sistema necesarios para OCR y PDF
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-spa \
    poppler-utils \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Directorio de la app
WORKDIR /app

# Reqs antes para cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar proyecto
COPY . /app/

# Variables útiles para OCR (opcional)
ENV TESSERACT_LANG=spa+eng \
    TESSERACT_PSM=6 \
    TESSERACT_PSM_IMAGE=4

# Comando por defecto (lo sobreescribe docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
