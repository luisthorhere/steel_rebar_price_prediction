# Imagen base ligera de Python
FROM python:3.10-slim

# Evitar que Python genere archivos .pyc y usar buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crear directorio de trabajo
WORKDIR /app

# Copiar solo los archivos necesarios primero (para aprovechar caché de Docker)
COPY requirements.txt .

# Instalar dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente
COPY . .

# Exponer el puerto donde correrá FastAPI
EXPOSE 8080

# Comando para ejecutar la app
# Cambia "src.main:app" si tu archivo principal tiene otro nombre
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]