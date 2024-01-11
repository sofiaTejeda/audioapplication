from flask import Flask, request
import threading
import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaIoBaseUpload
import io
from pydub import AudioSegment
import speech_recognition as sr
import whisper
import subprocess
import glob
from flask import jsonify


SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = '1Sbgn-laCEDDr3ak-cbC_SKrqGUMSSjWn'
app = Flask(__name__)

@app.route('/descargar', methods=['GET'])
def descargar_archivo():
    
    file_id = request.args.get('file_id')
    creds = None
    creds = service_account.Credentials.from_service_account_file(
        "token.json", scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)
    CONTAINER_DOWNLOAD_FOLDER = '/app/descargas'
    os.makedirs(CONTAINER_DOWNLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(CONTAINER_DOWNLOAD_FOLDER, "descargado.wav")
    google_request = service.files().get_media(fileId=file_id)
    file = service.files().get(fileId=file_id).execute()
    filename = file['name']
    print(filename)
    file_name = "descargado.wav"
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, google_request)
    done = False
    while not done:
        status, done = downloader.next_chunk()   
        print("Download %d%%." % int(status.progress() * 100))
1111
    # Guardar el archivo descargado
    with io.open(file_path, 'wb') as f:
        fh.seek(0)
        data = fh.read()
        print(f"Tamaño del buffer descargado: {len(data)} bytes")
        f.write(data)

    ruta_archivo_descargado = '/app/descargas/descargado.wav'
    dividir_audio_ffmpeg(ruta_archivo_descargado, 30)
    segmentos = listar_segmentos('/app/descargas', 'descargado')
    print("imprimiendo segmentos")
    print(segmentos)
    transcribirsegmento(segmentos)
    return jsonify(segmentos)

    # Dividir el archivo en segmentos
    #segmentos = dividir_audio(ruta_archivo_descargado)

    # Transcribir los segmentos
    #transcripciones = transcribir_segmentos(segmentos)

    # Hacer algo con las transcripciones, por ejemplo, unirlas en una sola cadena
    #texto_completo = ' '.join(transcripciones)

    # Devolver la transcripción completa
    #numero_segmen111111tos = len(segmentos)
    # transcribir_y_guardar(segmentos,filename, creds)
   
    #transcripciones = transcribir_segmento(segmentos[0])

    #return f"El archivo de audio fue dividido en {numero_segmentos} segmentos"
#    return "Transcripción iniciada en segundo plano"


def listar_segmentos(ruta_directorio, nombre_base):
    # Listar todos los archivos de segmento
    ruta_patron = os.path.join(ruta_directorio, f'{nombre_base}_*.wav')
    lista_archivos = glob.glob(ruta_patron)
    return lista_archivos

def dividir_audio_ffmpeg(ruta_archivo_origen, duracion_segmento_segundos=30):
    nombre_archivo_base = os.path.splitext(ruta_archivo_origen)[0]
    comando_ffmpeg = [
        'ffmpeg',
        '-i', ruta_archivo_origen,
        '-f', 'segment',
        '-segment_time', str(duracion_segmento_segundos),
        '-c', 'copy',
        f'{nombre_archivo_base}_%03d.wav'
    ]

    try:
        subprocess.run(comando_ffmpeg, check=True)
        print(f'Archivo {ruta_archivo_origen} dividido en segmentos de {duracion_segmento_segundos} segundos.')
    except subprocess.CalledProcessError as e:
        print(f'Ocurrió un error al dividir el archivo: {e}')

def transcribir_y_guardar(segmentos,file_name, creds):
    # Dividir el archivo en segmentos

    # Transcribir cada segmento
    transcripciones =transcribirsegmento(segmentos)

    # Unir las transcripciones en un solo texto
    texto_completo = '\n'.join(transcripciones)

    # Guardar el texto en Google Drive
    guardar_en_drive(texto_completo, file_name,creds)


def guardar_en_drive(texto,file_name, creds):
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {
        'name': file_name+'.txt',
        'mimeType': 'text/plain',
        'parents': ['1Sbgn-laCEDDr3ak-cbC_SKrqGUMSSjWn']
    }
    media = MediaIoBaseUpload(io.StringIO(texto), mimetype='text/plain', resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print("Archivo guardado en Drive con ID: {}".format(file.get('id')))

def iniciar_transcripcion_en_fondo(segmentos,file_name, creds):
    thread = threading.Thread(target=transcribir_y_guardar, args=(segmentos,file_name, creds))
    thread.start()

def transcribir_segmento(segmento):
    """Transcribe un único segmento de audio."""
    r = sr.Recognizer()
    nombre_archivo_temporal = "segmento_temporal.wav"
    segmento.export(nombre_archivo_temporal, format="wav")

    with sr.AudioFile(nombre_archivo_temporal) as source:
        audio = r.record(source)
        try:
            transcripcion = r.recognize_google(audio, language='es-ES')
            return transcripcion
        except sr.UnknownValueError:
            # El audio no se pudo entender
            return ''
        except sr.RequestError as e:
            # La API de reconocimiento no estuvo disponible
            return str(e)
        finally:
            # Eliminar el archivo de segmento temporal
            if os.path.exists(nombre_archivo_temporal):
                os.remove(nombre_archivo_temporal)   

def dividir_audio(ruta_archivo, duracion_segmento_ms=60000):
    duracion_segmento = 30 * 60 * 1000

    """Divide el archivo de audio en segmentos de duración especificada."""
    print("dividiendo primer segmento")
    audio = AudioSegment.from_file(ruta_archivo)
    longitud = len(audio)
    segmentos = [audio[i:i+duracion_segmento] for i in range(0, longitud, duracion_segmento)]
    # Suponiendo que ya tienes la lista 'segmentos' definida
    primer_segmento = [segmentos[0]]

    return primer_segmento


def transcribirsegmento(segmentos):
    transcripciones = []
    model = whisper.load_model("small")

    for i, segmento in enumerate(segmentos):
        # Guardar segmento temporal
        try:
                #transcripcion = r.recognize_google(audio, language='es-ES')
                transcripcion= model.transcribe(segmento, language="es")
                print(transcripcion["text"])
                transcripciones.append(transcripcion["text"])
        except Exception as e:
            # Manejar la excepción
                print(f"Ocurrió un error: {e}")
        # Eliminar el archivo de segmento temporal
        #os.remove(nombre_archivo_temporal)

    return transcripciones


def transcribir_segmentos(segmentos):
    """Transcribe una lista de segmentos de audio."""
    r = sr.Recognizer()
    transcripciones = []

    for i, segmento in enumerate(segmentos):
        # Guardar segmento temporal
        nombre_archivo_temporal = f"segmento_{i}.wav"
        segmento.export(nombre_archivo_temporal, format="wav")
        
        # Transcribir el segmento
        with sr.AudioFile(nombre_archivo_temporal) as source:
            #audio = r.record(source)
            try:
                #transcripcion = r.recognize_google(audio, language='es-ES')
                transcripcion=model = whisper.load_model("small")

                transcripciones.append(transcripcion)
            except sr.UnknownValueError:
                # El audio no se pudo entender
                transcripciones.append('')
            except sr.RequestError as e:
                # La API de reconocimiento no estuvo disponible
                transcripciones.append(str(e))

        # Eliminar el archivo de segmento temporal
        os.remove(nombre_archivo_temporal)

    return transcripciones

@app.route('/descargar2', methods=['GET'])
def descargar_archivo2():
    file_id = request.args.get('file_id')
    creds = service_account.Credentials.from_service_account_file(
        "token.json", scopes=SCOPES)

    service = build('drive', 'v3', credentials=creds)

    # Copiar el archivo a la nueva carpeta
    file_metadata = {
        'parents': [FOLDER_ID]  # Añadir el ID de la carpeta de destino
    }

    # Realiza la copia del archivo en Google Drive
    copied_file = service.files().copy(fileId=file_id, body=file_metadata).execute()

    # Retorna el nombre del archivo copiado y su ID para confirmar que se ha realizado la acción
    return f"Archivo '{copied_file.get('name')}' copiado con éxito en la carpeta con ID {FOLDER_ID}"


if __name__ == '__main__':
    app.run(debug=True)