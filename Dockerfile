# Imagen base
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos
COPY ./requirements.txt /app/requirements.txt

# Instala las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el proyecto
COPY ./ /app

# Expone el puerto para el servidor de desarrollo
EXPOSE 8000

# Comando para iniciar el servidor Django
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "myproject.wsgi:application"]


