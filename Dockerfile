# Dockerfile para Django
FROM python:3.10-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requisitos y lo instala
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación en /app
COPY . /app/

# Expone el puerto 8000 (opcional, ya que Nginx manejará el tráfico)
EXPOSE 8000

# Ejecuta Gunicorn para servir la aplicación Django
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "nombre_proyecto.wsgi:application"]

#--------------------------
# nginx/nginx.conf
server {
    listen 80;

    # Servir archivos estáticos
    location /static/ {
        alias /app/static/;
    }

    # Redirige las solicitudes a Gunicorn
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

#--------------------------