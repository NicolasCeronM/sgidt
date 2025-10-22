# ---------- Etapa build ----------
FROM python:3.12-slim AS builder
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Paquetes de compilación para wheels (lxml, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev libxslt1-dev zlib1g-dev libffi-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels


# ---------- Etapa runtime ----------
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    TZ=America/Santiago \
    # Para el warning de Celery 6 (opcional, no rompe nada si no lo usas):
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=1 \
    # Tesseract datos (ruta estándar en Debian Bookworm)
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Dependencias nativas:
# - WeasyPrint (cairo/pango/etc.)
# - OCR: tesseract + español
# - Poppler para pdf2image (pdftoppm)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    # WeasyPrint
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 libffi8 libxml2 libxslt1.1 \
    libjpeg62-turbo libpng16-16 fontconfig \
    fonts-dejavu-core fonts-liberation fonts-noto-color-emoji \
    # OCR
    tesseract-ocr tesseract-ocr-spa \
    # PDF -> imágenes
    poppler-utils \
    # zona horaria
    tzdata \
 && rm -rf /var/lib/apt/lists/*

# Instala wheels construidos
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copia el proyecto
COPY . .

# Asegura que exista el directorio de media (por si lo necesitas en el contenedor)
RUN mkdir -p /app/media

# Puerto (opcional, informativo)
EXPOSE 8000

# Comando por defecto (prod). En dev el compose lo sobreescribe con runserver
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
