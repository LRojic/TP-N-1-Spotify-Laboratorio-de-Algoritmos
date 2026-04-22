"""
🎵 Reproductor de Música Profesional
Punto de entrada principal - Configuración y utilidades
"""

# ===== STANDARD LIB =====
import sys
import os
import threading
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# ===== THIRD PARTY =====
from dotenv import load_dotenv

# ===== PYQT5 =====
from PyQt5.QtWidgets import QApplication

# ===== AUDIO =====
try:
    from moviepy.editor import AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import imageio_ffmpeg
    FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = None

try:
    from pydub import AudioSegment
    if FFMPEG_EXE:
        AudioSegment.converter = FFMPEG_EXE
except ImportError:
    AudioSegment = None

# ===== BACKEND =====
from spotify_api import get_spotify_client, search_tracks
from libs.spotify_downloader import download_track
import player

# Silenciar warnings de librerías (como pydub)
import warnings
warnings.filterwarnings("ignore")  # silencia pydub y otros warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

# Configuración
load_dotenv()
SPOTIFY_CLIENT = get_spotify_client()
CARPETA_DESCARGAS = "downloads"
Path(CARPETA_DESCARGAS).mkdir(exist_ok=True)

import logging
logging.disable(logging.CRITICAL)  # silencia todos los loggers

# Colores (tema oscuro Apple Music)
COLORS = {
    'bg_primary':    '#121212',
    'bg_secondary':  '#1E1E1E',
    'bg_tertiary':   '#2E2E2E',
    'accent':        '#00BFFF',
    'text_primary':  '#FFFFFF',
    'text_secondary':'#B3B3B3',
    'border':        '#282828',
}

# ─────────────────────────────────────────────
# PLAYLISTS PREDEFINIDAS


PLAYLISTS = {
    "🎸 Rock Nacional": [
        {"nombre": "De Música Ligera",          "artista": "Soda Stereo",                             "url": "https://open.spotify.com/track/4it4NYn9wNqGV54joA6oN0"},
        {"nombre": "Ji Ji Ji",                  "artista": "Patricio Rey y sus Redonditos de Ricota", "url": "https://open.spotify.com/track/0VWBsKl936U9OO0zypvRCZ"},
        {"nombre": "Seminare",                  "artista": "Serú Girán",                              "url": "https://open.spotify.com/track/7yPsoib9EoQVmK3loJgptI"},
        {"nombre": "La Balsa",                  "artista": "Los Gatos",                               "url": "https://open.spotify.com/track/4J2xMy0kakU9sAin1uppxb"},
        {"nombre": "Mírenla",                   "artista": "Ciro y los Persas",                       "url": "https://open.spotify.com/track/0WuKq2LiraBFney78dzwoc"},
        {"nombre": "Como Alí",                  "artista": "Los Piojos",                              "url": "https://open.spotify.com/track/3yJKzKUDLo65qDDBDZm9im"},
        {"nombre": "Los Dinosaurios",           "artista": "Charly García",                           "url": "https://open.spotify.com/track/3VCKdfJAL8DTDlwZw5O6Ik"},
        {"nombre": "Himno De Mi Corazón",       "artista": "Los Abuelos De La Nada",                  "url": "https://open.spotify.com/track/2kIhana7Cw57qXztsUb7NN"},
        {"nombre": "Ciudad Mágica",             "artista": "Tan Bionica",                             "url": "https://open.spotify.com/track/3YOWpKcFHDTqwSzvzRuSmR"},
        {"nombre": "Cae el Sol",                "artista": "Airbag",                                  "url": "https://open.spotify.com/track/1Mqfdem6pgGVoULjSkkcc9"},
    ],
     "🎵 Pop 2000s": [
        {"nombre": "Toxic",            "artista": "Britney Spears",  "url": "https://open.spotify.com/track/6I9VzXrHxO9rA9A5euc8Ak"},
        {"nombre": "Umbrella",         "artista": "Rihanna",         "url": "https://open.spotify.com/track/49FYlytm3dAAraYgpoJZux"},
        {"nombre": "Moves Like Jagger","artista": "Maroon 5",        "url": "https://open.spotify.com/track/2bL2gyO6kBdLkNSkxXNh6x"},
        {"nombre": "Poker Face",       "artista": "Lady Gaga",       "url": "https://open.spotify.com/track/1QV6tiMFM6fSOKOGLMHYYg"},
        {"nombre": "Hips Don't Lie",   "artista": "Shakira",         "url": "https://open.spotify.com/track/3d0WouFnFmr0K3kjeza3fF"},
        {"nombre": "Hot N Cold",       "artista": "Katy Perry",      "url": "https://open.spotify.com/track/1TEjSXPdAakDotj2Wji3PU"},
        {"nombre": "Single Ladies",    "artista": "Beyoncé",         "url": "https://open.spotify.com/track/5R9a4t5t5O0IsznsrKPVro"},
        {"nombre": "I Gotta Feeling",  "artista": "Black Eyed Peas", "url": "https://open.spotify.com/track/4kLLWz7srcuLKA7Et40PQR"},
        {"nombre": "Right Round",      "artista": "Flo Rida",        "url": "https://open.spotify.com/track/3GpbwCm3YxiWDvy29Uo3vP"},
        {"nombre": "Timber",           "artista": "Pitbull ft Kesha","url": "https://open.spotify.com/track/3cHyrEgdyYRjgJKSOiOtcS"},
    ],
}
PLAYLIST_COVERS = {
    "🎸 Rock Nacional": "assets/rock nacional portada.jpg",
    "🎵 Pop 2000s":     "assets/pop of the 2000s.jpg",
}
# ─────────────────────────────────────────────
# FUNCIONES DE UTILIDAD
# ─────────────────────────────────────────────

def buscar_canciones_locales(query):
    """Busca canciones en la carpeta downloads"""
    print(f"\n   🔍 Buscando localmente: '{query}'")
    canciones = []
    q = query.lower()

    for root_dir, dirs, files in os.walk(CARPETA_DESCARGAS):
        for archivo in files:
            if archivo.lower().endswith(('.mp3', '.wav', '.webm')):
                if q in archivo.lower() or q in os.path.basename(root_dir).lower():
                    ruta_completa = os.path.join(root_dir, archivo)
                    canciones.append({
                        'name': os.path.splitext(archivo)[0],
                        'path': ruta_completa,
                        'local': True
                    })
                    print(f"      ✅ Encontrada: {archivo}")

    if not canciones:
        print(f"      ❌ No se encontraron archivos locales")
    return canciones


def convertir_a_mp3(ruta_original):
    """Convierte cualquier archivo a MP3 usando moviepy, pydub o ffmpeg."""
    if ruta_original.lower().endswith(".mp3"):
        return ruta_original

    ruta_mp3 = os.path.splitext(ruta_original)[0] + ".mp3"

    if MOVIEPY_AVAILABLE:
        try:
            clip = AudioFileClip(ruta_original)
            clip.write_audiofile(ruta_mp3, logger=None)
            clip.close()
            return ruta_mp3
        except Exception:
            pass

    if AudioSegment and FFMPEG_EXE:
        try:
            audio = AudioSegment.from_file(ruta_original)
            audio.export(ruta_mp3, format="mp3")
            return ruta_mp3
        except Exception:
            pass

    if FFMPEG_EXE:
        try:
            subprocess.run(
                [FFMPEG_EXE, "-y", "-i", ruta_original, ruta_mp3],
                check=True,
                capture_output=True,
            )
            return ruta_mp3
        except Exception:
            pass

    return ruta_original

def descargar_playlists(on_progress=None):
    def worker():
        for nombre_playlist, tracks in PLAYLISTS.items():
            print(f"\n📋 Playlist: {nombre_playlist}")
            for track in tracks:
                nombre  = track['nombre']
                artista = track['artista']

                # Revisar si ya existe
                nombre_carpeta = f"{artista} - {nombre}"
                carpeta = os.path.join(CARPETA_DESCARGAS, nombre_carpeta)
                ya_existe = False
                if os.path.exists(carpeta):
                    for f in os.listdir(carpeta):
                        if f.lower().endswith(('.mp3', '.wav', '.webm')):
                            ya_existe = True
                            break

                if ya_existe:
                    print(f"   ✅ Ya existe: {artista} - {nombre}")
                    continue

                msg = f"⬇️ {artista} - {nombre}..."
                print(f"   {msg}")
                if on_progress:
                    on_progress(msg)

                try:
                    descargar_desde_spotify({
                        'name': nombre,
                        'external_urls': {'spotify': track['url']}
                    })
                    if on_progress:
                        on_progress(f"✅ Lista: {nombre}")
                except Exception as e:
                    print(f"   ❌ Error en {nombre}: {e}")

        if on_progress:
            on_progress("✅ Todas las playlists listas")

    threading.Thread(target=worker, daemon=True).start()

def descargar_desde_spotify(track):
    """Descarga una canción desde Spotify usando spotify_dl"""
    try:
        url = track['external_urls']['spotify']

        nombre_track = track.get('name', 'cancion').replace('/', '_').replace('\\', '_')
        carpeta_descarga = os.path.join(CARPETA_DESCARGAS, nombre_track)
        os.makedirs(carpeta_descarga, exist_ok=True)

        ruta = download_track(SPOTIFY_CLIENT, url, CARPETA_DESCARGAS)

        return ruta

    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {e}")
        return None
    
def obtener_duracion(ruta_archivo):
    """Obtiene la duración de un archivo de audio en segundos"""
    if MOVIEPY_AVAILABLE:
        try:
            clip = AudioFileClip(ruta_archivo)
            duracion = int(clip.duration)
            clip.close()
            return duracion
        except Exception:
            pass

    if AudioSegment:
        try:
            audio = AudioSegment.from_file(ruta_archivo)
            return int(len(audio) / 1000)
        except Exception:
            pass

    # Fallback: usar ffprobe si está disponible
    try:
        import imageio_ffmpeg
        ffprobe = imageio_ffmpeg.get_ffmpeg_exe().replace('ffmpeg', 'ffprobe')
        result = subprocess.run(
            [ffprobe, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', ruta_archivo],
            capture_output=True, text=True
        )
        return int(float(result.stdout.strip()))
    except Exception:
        pass

    # Último recurso: ffmpeg de imageio para leer duración
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        result = subprocess.run(
            [ffmpeg_exe, '-i', ruta_archivo],
            capture_output=True, text=True
        )
        # buscar "Duration: HH:MM:SS" en stderr
        import re
        match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)', result.stderr)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return h * 3600 + m * 60 + s
    except Exception:
        pass

    return 0

def buscar_cancion_playlist(nombre: str, artista: str) -> Optional[str]:
    """Busca exactamente 'Artista - Nombre' — solo para playlists"""
    nombre_carpeta = f"{artista} - {nombre}"
    carpeta = os.path.join(CARPETA_DESCARGAS, nombre_carpeta)
    if os.path.exists(carpeta):
        # Preferir mp3 sobre webm
        for ext in ('.mp3', '.wav', '.webm'):
            for f in os.listdir(carpeta):
                if f.lower().endswith(ext):
                    return os.path.join(carpeta, f)
    return None


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    from music_player import MusicPlayer
    
    app = QApplication(sys.argv)
    app.setApplicationName("🎵 Reproductor de Música")
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
#C:\Users\karin\OneDrive\Documentos\GitHub\python-con-nacho\Trabajo-practico-N-1---Laboratorio-de-Algoritmos\main.py