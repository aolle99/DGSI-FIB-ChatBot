FROM python:3.13-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar los archivos de requisitos primero para aprovechar el caché de capas de Docker
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Crear directorio para la base de datos SQLite (si se usa SQLite)
RUN mkdir -p /app/data

# Exponer el puerto en el que corre la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]