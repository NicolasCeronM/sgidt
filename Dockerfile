# ---------- Etapa build ----------
FROM python:3.12-slim AS builder
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# ---------- Etapa runtime ----------
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Dependencias nativas requeridas por WeasyPrint (Debian/Bookworm)
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    libpng16-16 \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    fonts-noto-color-emoji \
 && rm -rf /var/lib/apt/lists/*

# Instala wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/*

# Copia proyecto
COPY . .

# Comando por defecto (prod). En dev el compose lo sobreescribe con runserver
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
