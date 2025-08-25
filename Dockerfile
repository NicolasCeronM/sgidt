FROM python:3.12-slim


WORKDIR /code


# Dependencias del SO necesarias para OCR/PDF
RUN apt-get update && apt-get install -y \
build-essential \
tesseract-ocr \
tesseract-ocr-spa \
poppler-utils \
libglib2.0-0 \
libgl1 \
&& rm -rf /var/lib/apt/lists/*


# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Proyecto
COPY . .


EXPOSE 8000