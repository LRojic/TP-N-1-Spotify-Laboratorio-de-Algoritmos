import os
import threading
from pathlib import Path
import tkinter as tk
from tkinter import Listbox, Label, Frame
from dotenv import load_dotenv
from moviepy import AudioFileClip

from spotify_api import get_spotify_client, search_tracks
from PIL import Image, ImageTk
import requests
from io import BytesIO

from libs.spotify_downloader import download_track

import player  # mover al inicio

# ────────── CONFIGURACIÓN ──────────
load_dotenv()
sp = get_spotify_client()
CARPETA_DESCARGAS = "downloads"
os.makedirs(CARPETA_DESCARGAS, exist_ok=True)

# Variables globales
cancion_actual = None
duracion_total = 0
reproduciendo = False
# ────────── FUNCIONES ──────────
def formatear_tiempo(segundos):
    minutos = int(segundos // 60)
    segs = int(segundos % 60)
    return f"{minutos}:{segs:02d}"

def mostrar_imagen(url):
    try:
        response = requests.get(url)
        img_data = response.content

        img = Image.open(BytesIO(img_data))
        img = img.resize((200, 200))  # tamaño

        img_tk = ImageTk.PhotoImage(img)

        cover_label.config(image=img_tk)
        cover_label.image = img_tk  # evitar garbage collector

    except Exception as e:
        print("Error cargando imagen:", e)

    
def actualizar_barra():
    global reproduciendo

    if reproduciendo and not is_paused:
        try:
            pos = player.get_pos()

            if pos >= 0:
                progress.set(pos)

                tiempo_actual = formatear_tiempo(pos)
                tiempo_total = formatear_tiempo(duracion_total)

                tiempo_label.config(text=f"{tiempo_actual} / {tiempo_total}")

        except:
            pass

    root.after(500, actualizar_barra)
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
            nombre = f"{t['name']} - {t['artists'][0]['name']} ({t['album']})"
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
        log_estado(f"✅ Convertido a MP3: {ruta_mp3}")
        return ruta_mp3
    except Exception as e:
        print(f"❌ Error convirtiendo a MP3: {e}")
        log_estado(f"❌ Error convirtiendo a MP3: {e}")
        return ruta_original  # fallback
def reproducir(event):
    global is_paused, duracion_total, reproduciendo

    is_paused = False
    btn_play.config(text="⏸️")
    reproduciendo = True

    index = resultados.curselection()
    if not index:
        return

    track = resultados.track_data[index[0]]

    

        # Mostrar portada si existe
    if not track.get('local') and track.get('image'):
        mostrar_imagen(track['image'])

    # ────────── LOCAL ──────────
    if track.get('local'):
        ruta = convertir_a_mp3(track['path'])

        try:
            clip = AudioFileClip(ruta)
            duracion_total = int(clip.duration)
            clip.close()

            root.after(0, lambda: progress.config(to=duracion_total))
            root.after(0, lambda: tiempo_label.config(
                text=f"0:00 / {formatear_tiempo(duracion_total)}"
            ))

            reproduciendo = True
            log_estado("▶️ Reproduciendo canción local")

        except Exception as e:
            log_estado(f"❌ Error leyendo duración: {e}")

        threading.Thread(
            target=player.reproducir,
            args=(ruta,),
            daemon=True
        ).start()

    # ────────── SPOTIFY / DESCARGA ──────────
    else:
        def descargar_y_reproducir():
            global duracion_total, reproduciendo

            try:
                log_estado("⬇️ Descargando canción...")

                url = track['external_urls']['spotify']
                ruta_descarga = download_track(sp, url, CARPETA_DESCARGAS)

                if ruta_descarga:
                    for f in os.listdir(ruta_descarga):
                        if f.lower().endswith(('.mp3', '.wav', '.webm')):
                            ruta_completa = os.path.join(ruta_descarga, f)
                            ruta_mp3 = convertir_a_mp3(ruta_completa)

                            # 🎧 calcular duración
                            try:
                                clip = AudioFileClip(ruta_mp3)
                                duracion_total = int(clip.duration)
                                clip.close()

                                root.after(0, lambda: progress.config(to=duracion_total))
                                root.after(0, lambda: tiempo_label.config(
                                    text=f"0:00 / {formatear_tiempo(duracion_total)}"
                                ))

                                reproduciendo = True

                            except Exception as e:
                                log_estado(f"❌ Error leyendo duración: {e}")

                            log_estado("🎵 Reproduciendo canción descargada")
                            player.reproducir(ruta_mp3)
                            break
                else:
                    log_estado("❌ No se pudo descargar")

            except Exception as e:
                log_estado(f"❌ Error: {e}")

        threading.Thread(target=descargar_y_reproducir, daemon=True).start()
# ────────── INTERFAZ import tkinter as tk
import tkinter as tk
from tkinter import Listbox, Label, Frame

# ────────── CONFIG COLORES ──────────
BG_COLOR = "#121212"
CARD_COLOR = "#181818"
ACCENT = "#00BFFF"  # azul eléctrico
TEXT = "#FFFFFF"
SUBTEXT = "#B3B3B3"

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_NORMAL = ("Segoe UI", 13)
FONT_SMALL = ("Segoe UI", 11)

# ────────── ESTADO PLAYER ──────────
is_paused = False

def toggle_play():
    global is_paused, reproduciendo

    if reproduciendo:
        if is_paused:
            player.reanudar()
            btn_play.config(text="⏸️")
            log_estado("▶️ Reproduciendo")
            is_paused = False
        else:
            player.pausar()
            btn_play.config(text="▶️")
            log_estado("⏸️ Pausado")
            is_paused = True

# ────────── ROOT ──────────
root = tk.Tk()
root.title("Reproductor de Música - Offline/Online")
root.geometry("900x550")
root.configure(bg=BG_COLOR)

# ────────── TOP FRAME (Buscador + Imagen) ──────────
top_frame = Frame(root, bg=BG_COLOR)
top_frame.pack(pady=10, fill=tk.X, padx=10)

# ────────── BUSCADOR ──────────
search_frame = Frame(top_frame, bg=BG_COLOR)
search_frame.pack(side=tk.LEFT)

Label(search_frame, text="🔍 Buscar:", bg=BG_COLOR, fg=TEXT, font=FONT_TITLE).pack(side=tk.LEFT, padx=10)

entry = tk.Entry(
    search_frame,
    width=25,
    font=("Segoe UI", 14),
    bg=CARD_COLOR,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat"
)
entry.pack(side=tk.LEFT, padx=10, ipady=5)

tk.Button(
    search_frame,
    text="Buscar",
    command=buscar,
    bg=ACCENT,
    fg="black",
    font=FONT_NORMAL,
    activebackground="#33ccff",
    relief="flat",
    padx=10
).pack(side=tk.LEFT, padx=5)

# ────────── ALBUM COVER (derecha del top) ──────────
cover_label = Label(top_frame, bg=BG_COLOR)
cover_label.pack(side=tk.RIGHT, padx=10)

# ────────── ESTADO ──────────
estado_label = Label(
    root,
    text="⏹️ Listo",
    fg=ACCENT,
    bg=BG_COLOR,
    font=FONT_NORMAL
)
estado_label.pack(pady=5)

def log_estado(msg):
    print(msg)
    try:
        estado_label.after(0, lambda: estado_label.config(text=msg))
    except:
        pass

# ────────── CONTROLES ──────────
control_frame = Frame(root, bg=BG_COLOR)
control_frame.pack(pady=5)

Label(
    control_frame,
    text="CONTROLES",
    bg=BG_COLOR,
    fg=TEXT,
    font=FONT_TITLE
).pack()

Label(
    control_frame,
    text="Doble Click = Reproducir",
    bg=BG_COLOR,
    fg=SUBTEXT,
    font=FONT_SMALL
).pack()

info_label = Label(control_frame, text="", bg=BG_COLOR, fg=TEXT, font=FONT_NORMAL)
info_label.pack(pady=(0, 8))

# Botones
botones_frame = Frame(control_frame, bg=BG_COLOR)
botones_frame.pack(pady=2)

btn_style = {
    "font": FONT_NORMAL,
    "bg": CARD_COLOR,
    "fg": TEXT,
    "activebackground": ACCENT,
    "activeforeground": "black",
    "relief": "flat",
    "padx": 12,
    "pady": 5
}

# 🔥 BOTÓN TOGGLE (play/pausa)
btn_play = tk.Button(botones_frame, text="⏸️", command=toggle_play, **btn_style)
btn_play.grid(row=0, column=0, padx=5)

progress = tk.Scale(
    control_frame,
    from_=0,
    to=100,
    orient="horizontal",
    length=500,
    bg=BG_COLOR,
    fg=TEXT,
    troughcolor=CARD_COLOR,
    highlightthickness=0,
    bd=0
)
progress.pack(pady=5)

tiempo_label = tk.Label(
    control_frame,
    text="0:00 / 0:00",
    bg=BG_COLOR,
    fg=SUBTEXT,
    font=("Segoe UI", 11)
)
tiempo_label.pack()

# ────────── RESULTADOS ──────────
Label(
    root,
    text="Resultados (Doble click para reproducir):",
    bg=BG_COLOR,
    fg=TEXT,
    font=FONT_TITLE
).pack(anchor="w", padx=15)

resultados = Listbox(
    root,
    width=70,
    height=12,
    bg=CARD_COLOR,
    fg=TEXT,
    font=("Segoe UI", 13),
    selectbackground=ACCENT,
    selectforeground="black",
    relief="flat",
    bd=0,
    highlightthickness=0
)

resultados.pack(pady=10, padx=15, fill="both", expand=True)

resultados.bind("<Double-1>", reproducir)

# ────────── RUN 

actualizar_barra()
root.mainloop()