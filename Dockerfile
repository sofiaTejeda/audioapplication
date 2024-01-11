# Usa una imagen base de Python
FROM python:3.8

# Establece el directorio de trabajo
WORKDIR /app

# Actualiza los paquetes e instala ffmpeg
RUN apt-get update && \
    apt-get install -y python3-pip && \
    rm -rf /var/lib/apt/lists/*
RUN pip install proxy-requests
RUN pip install git+https://github.com/openai/whisper.git

RUN apt-get update && apt-get install ffmpeg -y
RUN pip install google-api-python-client google-auth-httplib2


# Copia los archivos de requisitos y los instala
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copia el resto del código de la aplicación
COPY app/ app/
# Copia el archivo run.py al directorio de trabajo en el contenedor
COPY run.py /app/
COPY token.json /app/
COPY credenciales.json /app/app
# Expone el puerto en el que se ejecutará Flask
EXPOSE 5000

# Establece el comando para ejecutar la aplicación
CMD ["python", "run.py"]
