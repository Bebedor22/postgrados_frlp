# Imagen del backend — Sistema de Posgrado (FastAPI + Python 3.12)
FROM python:3.12-slim

# Evita archivos .pyc y muestra los logs al instante
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias, así Docker reutiliza esta capa si no cambian.
# Es la imagen de desarrollo: incluye también pytest, para correr los tests adentro.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Después el código
COPY . .

# Carpeta interna para los PDFs (nunca expuesta como estática)
RUN mkdir -p /var/postgrado-storage

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]