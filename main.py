"""Reproductor de Música - Tkinter + Spotify + Reproducción Local Python Puro"""

import os
import sys

# ✅ Configurar FFmpeg ANTES de cualquier otra importación
try:
    import imageio_ffmpeg
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_path)
    # Agregar al PATH para que pydub lo encuentre
    os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
    print(f"✅ FFmpeg encontrado: {ffmpeg_path}")
except Exception as e:
    print(f"⚠️ No se pudo configurar FFmpeg: {e}")

import tkinter as tk
from tkinter import Listbox, Label, Frame
from dotenv import load_dotenv
from pathlib import Path
import threading
import sounddevice as sd
import numpy as np
from pydub import AudioSegment

# Agregar libs al path

from spotify_api import get_spotify_client, search_tracks
from spotify_downloader import download_track, sanitize_filename

# ────────── CONFIGURACIÓN ──────────
load_dotenv()
sp = get_spotify_client()
CARPETA_DESCARGAS = "downloads"
os.makedirs(CARPETA_DESCARGAS, exist_ok=True)

# Variables globales
cancion_actual = None
esta_pausada = False
stream_activo = None

# ────────── FUNCIONES ──────────
def buscar():
    """Busca canciones en Spotify y locales"""
    query = entry.get().strip()
    if not query:
        return
    
    resultados.delete(0, tk.END)
    resultados.track_data = []
    
    # 1. Buscar en canciones descargadas localmente
    canciones_locales = buscar_canciones_locales(query)
    for cancion in canciones_locales:
        resultados.insert(tk.END, f"💾 {cancion['name']}")
        resultados.track_data.append(cancion)
    
    # 2. Buscar en Spotify
    try:
        tracks = search_tracks(sp, query)
        for t in tracks:
            nombre = f"{t['name']} - {t['artists'][0]['name']}"
            resultados.insert(tk.END, f"🌐 {nombre}")
            resultados.track_data.append(t)
    except Exception as e:
        print(f"Error en búsqueda Spotify: {e}")


def buscar_canciones_locales(query):
    """Busca canciones descargadas en la carpeta downloads"""
    canciones = []
    query_lower = query.lower()
    
    if not os.path.exists(CARPETA_DESCARGAS):
        return canciones
    
    for carpeta in os.listdir(CARPETA_DESCARGAS):
        ruta = os.path.join(CARPETA_DESCARGAS, carpeta)
        if os.path.isdir(ruta):
            if query_lower in carpeta.lower():
                # Buscar archivos de audio
                for archivo in os.listdir(ruta):
                    if archivo.endswith(('.mp3', '.webm', '.wav', '.ogg', '.opus', '.flac')):
                        canciones.append({
                            'name': carpeta,
                            'path': os.path.join(ruta, archivo),
                            'local': True
                        })
                        break
    
    return canciones


def reproducir_pydub(ruta_archivo):
    """Reproduce audio con pydub + sounddevice (soporta todos los formatos con FFmpeg)"""
    global cancion_actual, esta_pausada, stream_activo
    
    try:
        nombre_cancion = Path(ruta_archivo).parent.name
        estado_label.config(text=f"▶️ Cargando: {nombre_cancion}")
        root.update()
        
        # Cargar archivo con pydub (soporta WebM, MP3, WAV, FLAC, OGG, etc.)
        print(f"📂 Cargando archivo: {Path(ruta_archivo).name}")
        
        # Obtener ffmpeg_path si está disponible
        ffmpeg_path = None
        try:
            import imageio_ffmpeg
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        except:
            pass
        
        # Cargar audio
        if ffmpeg_path:
            audio = AudioSegment.from_file(
                ruta_archivo,
                parameters=["-threads", "1"]
            )
        else:
            audio = AudioSegment.from_file(ruta_archivo)
        
        # Convertir a numpy array
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        
        # Si es estéreo, reshape a (N, 2)
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
        elif audio.channels > 2:
            samples = samples.reshape((-1, audio.channels))
        
        # Normalizar audio
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = samples / max_val
        
        cancion_actual = ruta_archivo
        esta_pausada = False
        
        estado_label.config(text=f"▶️ Reproduciendo: {nombre_cancion}")
        
        # Reproducir con sounddevice
        stream_activo = sd.play(samples, audio.frame_rate)
        sd.wait()
        
        # Cuando termina
        if cancion_actual == ruta_archivo:
            estado_label.config(text="✓ Reproducción completada")
        
        stream_activo = None
        
    except Exception as e:
        msg = f"❌ Error: {str(e)[:50]}"
        estado_label.config(text=msg)
        print(f"Error reproduciendo: {e}")


def detener_actual():
    """Detiene la canción actual"""
    global cancion_actual, stream_activo
    try:
        if stream_activo:
            sd.stop()
    except:
        pass
    cancion_actual = None


def reproducir(event):
    """Maneja doble click: reproduce local o descarga de Spotify"""
    global cancion_actual
    
    index = resultados.curselection()
    if not index:
        return
    
    index = index[0]
    track = resultados.track_data[index]
    
    detener_actual()
    
    # Si es local, reproduce directamente
    if track.get('local'):
        # Reproducir en hilo para no bloquear UI
        thread = threading.Thread(target=reproducir_pydub, args=(track['path'],), daemon=True)
        thread.start()
    else:
        # Si es de Spotify, descarga en hilo aparte
        def descargar_y_reproducir():
            try:
                url_spotify = track['external_urls']['spotify']
                resultado = download_track(sp, url_spotify, CARPETA_DESCARGAS)
                
                if resultado:
                    # Buscar el archivo descargado
                    for archivo in os.listdir(resultado):
                        if archivo.endswith(('.mp3', '.webm', '.wav', '.ogg', '.opus', '.flac')):
                            ruta_completa = os.path.join(resultado, archivo)
                            reproducir_pydub(ruta_completa)
                            break
                else:
                    estado_label.config(text="❌ No se pudo descargar")
            except Exception as e:
                estado_label.config(text=f"❌ Error: {e}")
                print(f"Error: {e}")
        
        # Ejecutar descarga en hilo para no bloquear UI
        thread = threading.Thread(target=descargar_y_reproducir, daemon=True)
        thread.start()


def pausar_reanudar(event=None):
    """Pausa o reanuda con la barra espaciadora"""
    global esta_pausada, stream_activo
    
    if not stream_activo:
        return
    
    try:
        if esta_pausada:
            sd.resume()
            esta_pausada = False
            estado_label.config(text="▶️ Reanudando...")
        else:
            sd.pause()
            esta_pausada = True
            estado_label.config(text="⏸️ Pausada")
    except:
        pass


# ────────── INTERFAZ ──────────
root = tk.Tk()
root.title("Reproductor de Música - Offline/Online")
root.geometry("600x500")

# Frame superior - búsqueda
search_frame = Frame(root)
search_frame.pack(pady=10)

label_buscar = Label(search_frame, text="🔍 Buscar:")
label_buscar.pack(side=tk.LEFT, padx=5)

entry = tk.Entry(search_frame, width=40)
entry.pack(side=tk.LEFT, padx=5)

boton_buscar = tk.Button(search_frame, text="Buscar", command=buscar)
boton_buscar.pack(side=tk.LEFT, padx=5)

# Frame de estado
estado_label = Label(root, text="⏹️ Listo", fg="blue", font=("Arial", 10))
estado_label.pack(pady=5)

# Lista de resultados
label_resultados = Label(root, text="Resultados (Doble click para reproducir):")
label_resultados.pack(anchor="w", padx=10)

resultados = Listbox(root, width=80, height=15)
resultados.pack(pady=10, padx=10)
resultados.bind("<Double-1>", reproducir)

# Frame inferior - controles
control_frame = Frame(root)
control_frame.pack(pady=10)

Label(control_frame, text="CONTROLES:", font=("Arial", 10, "bold")).pack()
Label(control_frame, text="Espaciador = Pausa/Reanuda", font=("Arial", 9)).pack()
Label(control_frame, text="Doble Click = Reproducir", font=("Arial", 9)).pack()

# Bind tecla espacio
root.bind('<space>', pausar_reanudar)

# Ejecutar
root.mainloop()
detener_actual()