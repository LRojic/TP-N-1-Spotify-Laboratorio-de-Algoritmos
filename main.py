import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import Listbox, Label, Frame
from dotenv import load_dotenv
from moviepy import AudioFileClip

from spotify_api import get_spotify_client, search_tracks
from libs.spotify_downloader import download_track

import player  # mover al inicio

# ────────── CONFIGURACIÓN ──────────
load_dotenv()
sp = get_spotify_client()
CARPETA_DESCARGAS = "downloads"
os.makedirs(CARPETA_DESCARGAS, exist_ok=True)

# Variables globales
cancion_actual = None

# ────────── FUNCIONES ──────────
def buscar():
    query = entry.get().strip()
    if not query:
        return
    resultados.delete(0, tk.END)
    resultados.track_data = []

    # Buscar locales
    for cancion in buscar_canciones_locales(query):
        resultados.insert(tk.END, f"💾 {cancion['name']}")
        resultados.track_data.append(cancion)

    # Buscar Spotify
    try:
        for t in search_tracks(sp, query):
            nombre = f"{t['name']} - {t['artists'][0]['name']}"
            resultados.insert(tk.END, f"🌐 {nombre}")
            resultados.track_data.append(t)
    except Exception as e:
        print(f"Error en búsqueda Spotify: {e}")

def buscar_canciones_locales(query):
    canciones = []
    q = query.lower()
    for root_dir, dirs, files in os.walk(CARPETA_DESCARGAS):
        for archivo in files:
            if archivo.lower().endswith(('.mp3', '.wav', '.webm')):
                if q in archivo.lower() or q in os.path.basename(root_dir).lower():
                    canciones.append({
                        'name': os.path.splitext(archivo)[0],
                        'path': os.path.join(root_dir, archivo),
                        'local': True
                    })
    return canciones

def convertir_a_mp3(ruta_original):
    """Convierte cualquier archivo .webm a .mp3 usando moviepy + imageio-ffmpeg"""
    if ruta_original.lower().endswith(".mp3"):
        return ruta_original  # ya es mp3
    ruta_mp3 = os.path.splitext(ruta_original)[0] + ".mp3"
    try:
        clip = AudioFileClip(ruta_original)
        clip.write_audiofile(ruta_mp3, logger=None)
        clip.close()
        print(f"✅ Convertido a MP3: {ruta_mp3}")
        return ruta_mp3
    except Exception as e:
        print(f"❌ Error convirtiendo a MP3: {e}")
        return ruta_original  # fallback

def reproducir(event):
    index = resultados.curselection()
    if not index:
        return
    track = resultados.track_data[index[0]]

    if track.get('local'):
        ruta = convertir_a_mp3(track['path'])
        threading.Thread(target=player.reproducir, args=(ruta,), daemon=True).start()
    else:
        def descargar_y_reproducir():
            try:
                url = track['external_urls']['spotify']
                ruta_descarga = download_track(sp, url, CARPETA_DESCARGAS)
                if ruta_descarga:
                    for f in os.listdir(ruta_descarga):
                        if f.lower().endswith(('.mp3', '.wav', '.webm')):
                            ruta_completa = os.path.join(ruta_descarga, f)
                            ruta_mp3 = convertir_a_mp3(ruta_completa)
                            player.reproducir(ruta_mp3)
                            break
                else:
                    estado_label.config(text="❌ No se pudo descargar")
            except Exception as e:
                estado_label.config(text=f"❌ Error: {e}")
                print(f"Error: {e}")
        threading.Thread(target=descargar_y_reproducir, daemon=True).start()

# ────────── INTERFAZ ──────────
root = tk.Tk()
root.title("Reproductor de Música - Offline/Online")
root.geometry("600x500")

# Buscador
search_frame = Frame(root)
search_frame.pack(pady=10)
Label(search_frame, text="🔍 Buscar:").pack(side=tk.LEFT, padx=5)
entry = tk.Entry(search_frame, width=40)
entry.pack(side=tk.LEFT, padx=5)
tk.Button(search_frame, text="Buscar", command=buscar).pack(side=tk.LEFT, padx=5)

# Estado
estado_label = Label(root, text="⏹️ Listo", fg="blue", font=("Arial", 10))
estado_label.pack(pady=5)



# Resultados
Label(root, text="Resultados (Doble click para reproducir):").pack(anchor="w", padx=10)
resultados = Listbox(root, width=80, height=15)
resultados.pack(pady=10, padx=10)
resultados.bind("<Double-1>", reproducir)

# Controles
# ────────── CONTROLES ──────────
control_frame = Frame(root)
control_frame.pack(pady=10)

Label(control_frame, text="CONTROLES:", font=("Arial", 10, "bold")).pack()
Label(control_frame, text="Doble Click = Reproducir", font=("Arial", 9)).pack()

# Frame para botones
botones_frame = Frame(control_frame)
botones_frame.pack(pady=5)

# Botones
tk.Button(botones_frame, text="⏸️ Pausa", command=player.pausar).grid(row=0, column=0, padx=5)
tk.Button(botones_frame, text="▶️ Reanudar", command=player.reanudar).grid(row=0, column=1, padx=5)
tk.Button(botones_frame, text="⏹️ Stop", command=player.stop).grid(row=0, column=2, padx=5)
# Ejecutar
root.mainloop()