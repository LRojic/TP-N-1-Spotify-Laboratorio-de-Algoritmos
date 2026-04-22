"""
🎵 Reproductor de Música Profesional
Interfaz moderna tipo Apple Music - Python + PyQt5
Backend: Spotify API + pygame
"""

# ===== STANDARD LIB =====
import sys
import os
import threading
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict

# ===== THIRD PARTY =====
from dotenv import load_dotenv
from PIL import Image
import requests

# ===== PYQT5 =====
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QSlider, QComboBox, QScrollArea, QFrame, QTextEdit, QShortcut
    , QStackedWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QColor, QPixmap, QKeySequence

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

import warnings
warnings.filterwarnings("ignore")  # silencia pydub y otros warnings
# Configuración
load_dotenv()
SPOTIFY_CLIENT = get_spotify_client()
CARPETA_DESCARGAS = "downloads"
Path(CARPETA_DESCARGAS).mkdir(exist_ok=True)



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
        {"nombre": "Toxic",           "artista": "Britney Spears",  "url": "https://open.spotify.com/track/6I9VzXrHxO9rA9A5euc8Ak"},
        {"nombre": "Umbrella",        "artista": "Rihanna",         "url": "https://open.spotify.com/track/49FYlytm3dAAraYgpoJZux"},
        {"nombre": "Animals",         "artista": "Maroon 5",        "url": "https://open.spotify.com/track/2bL2gyO6kBdLkNSkxXNh6x"},
        {"nombre": "Poker Face",      "artista": "Lady Gaga",       "url": "https://open.spotify.com/track/1QV6tiMFM6fSOKOGLMHYYg"},
        {"nombre": "Hips Don't Lie",  "artista": "Shakira",         "url": "https://open.spotify.com/track/3d0WouFnFmr0K3kjeza3fF"},
        {"nombre": "Hot N Cold",      "artista": "Katy Perry",      "url": "https://open.spotify.com/track/1TEjSXPdAakDotj2Wji3PU"},
        {"nombre": "Single Ladies",   "artista": "Beyoncé",         "url": "https://open.spotify.com/track/5R9a4t5t5O0IsznsrKPVro"},
        {"nombre": "I Gotta Feeling", "artista": "Black Eyed Peas", "url": "https://open.spotify.com/track/4kLLWz7srcuLKA7Et40PQR"},
        {"nombre": "Right Round",     "artista": "Flo Rida",        "url": "https://open.spotify.com/track/3GpbwCm3YxiWDvy29Uo3vP"},
        {"nombre": "Timber",          "artista": "Pitbull ft Kesha","url": "https://open.spotify.com/track/3cHyrEgdyYRjgJKSOiOtcS"},
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
    print(f"   ⬇️ Descargando desde Spotify...")
    try:
        url = track['external_urls']['spotify']
        print(f"   📍 URL: {url}")

        nombre_track = track.get('name', 'cancion').replace('/', '_').replace('\\', '_')
        carpeta_descarga = os.path.join(CARPETA_DESCARGAS, nombre_track)
        os.makedirs(carpeta_descarga, exist_ok=True)

        ruta = download_track(SPOTIFY_CLIENT, url, CARPETA_DESCARGAS)
        print(f"   ✅ Descargada en: {ruta}")
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
# WIDGETS
# ─────────────────────────────────────────────

class SearchResultItem(QFrame):
    """Widget para mostrar resultado de búsqueda"""
    clicked = pyqtSignal(dict)

    def __init__(self, track: dict):
        super().__init__()
        self.track = track
        self.setStyleSheet(f'''
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_tertiary']};
            }}
        ''')
        self.setCursor(Qt.PointingHandCursor)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Imagen del álbum
        image_label = QLabel()
        image_label.setFixedSize(80, 80)
        image_label.setStyleSheet("border-radius: 4px; background-color: #333;")

        if self.track.get('image'):
            try:
                img_data = requests.get(self.track['image'], timeout=5).content
                pixmap = QPixmap()
                pixmap.loadFromData(img_data)
                scaled_pixmap = pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
            except Exception:
                image_label.setText("🎵")
                image_label.setAlignment(Qt.AlignCenter)
        else:
            image_label.setText("🎵")
            image_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(image_label)

        # Info del track
        info_layout = QVBoxLayout()

        name_label = QLabel(self.track.get('name', 'Unknown'))
        name_label.setFont(QFont('Arial', 11, QFont.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        info_layout.addWidget(name_label)

        artists = ', '.join([a.get('name', '') for a in self.track.get('artists', [])])
        artist_label = QLabel(artists)
        artist_label.setFont(QFont('Arial', 9))
        artist_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(artist_label)

        album_label = QLabel(self.track.get('album', 'Unknown Album'))
        album_label.setFont(QFont('Arial', 9))
        album_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(album_label)

        layout.addLayout(info_layout, 1)
        
        

        # Botón Play
        play_btn = QPushButton("▶ Play")
        play_btn.setFixedSize(80, 35)
        play_btn.setFont(QFont('Arial', 10, QFont.Bold))
        play_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {COLORS['accent']};
                color: black;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #33CCFF;
            }}
        ''')
        play_btn.clicked.connect(self._on_play)
        layout.addWidget(play_btn)

        self.setLayout(layout)

    def _on_play(self):
        self.clicked.emit(self.track)

    def mousePressEvent(self, event):
        self.clicked.emit(self.track)
        super().mousePressEvent(event)
class PlaylistView(QWidget):
    """Pantalla de canciones de una playlist"""

    def __init__(self, nombre_playlist: str, tracks: list, on_play, parent=None):
        super().__init__(parent)
        self.on_play = on_play
        self.track_rows = {}
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet(f"background-color: {COLORS['bg_secondary']};")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 15, 20, 15)

        back_btn = QPushButton("← Volver")
        back_btn.setFixedWidth(100)
        back_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: transparent;
                color: {COLORS['accent']};
                border: none;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{ color: #33CCFF; }}
        ''')
        back_btn.clicked.connect(lambda: parent.setCurrentIndex(1))
        header_layout.addWidget(back_btn)

        title = QLabel(nombre_playlist)
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)
        header_layout.addStretch()

        count = QLabel(f"{len(tracks)} canciones")
        count.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        header_layout.addWidget(count)

        header.setLayout(header_layout)
        layout.addWidget(header)

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(sep)

        # Lista de canciones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f'''
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg_secondary']}; width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']}; border-radius: 3px;
            }}
        ''')

        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        tracks_layout = QVBoxLayout()
        tracks_layout.setContentsMargins(20, 10, 20, 10)
        tracks_layout.setSpacing(2)

        for i, track in enumerate(tracks):
            row = self._create_track_row(i + 1, track)
            tracks_layout.addWidget(row)

        tracks_layout.addStretch()
        container.setLayout(tracks_layout)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)
        self.setLayout(layout)

    def _create_track_row(self, numero: int, track: dict) -> QFrame:
        row = QFrame()
        row.setObjectName(f"track_row_{numero}")
        row.setCursor(Qt.PointingHandCursor)
        row.setStyleSheet(f'''
            QFrame {{
                background-color: transparent;
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_secondary']};
            }}
        ''')

        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(15)

        num_label = QLabel(str(numero))
        num_label.setFixedWidth(25)
        num_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        num_label.setAlignment(Qt.AlignCenter)
        row_layout.addWidget(num_label)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_label = QLabel(track['nombre'])
        name_label.setFont(QFont('Arial', 11, QFont.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        info_layout.addWidget(name_label)

        artist_label = QLabel(track['artista'])
        artist_label.setFont(QFont('Arial', 9))
        artist_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(artist_label)

        row_layout.addLayout(info_layout, 1)

        play_btn = QPushButton("▶")
        play_btn.setFixedSize(32, 32)
        play_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {COLORS['accent']};
                color: black;
                border: none;
                border-radius: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #33CCFF; }}
        ''')
        play_btn.clicked.connect(lambda _, t=track, n=numero: (self.set_playing(n), self.on_play(t)))
        row_layout.addWidget(play_btn)

        row.setLayout(row_layout)
        self.track_rows[numero] = row  # guardar referencia
        return row
    def set_playing(self, numero: int):
        """Remarca la fila activa y desremarca las demás"""
        for n, row in self.track_rows.items():
            if n == numero:
                row.setStyleSheet(f'''
                    QFrame {{
                        background-color: {COLORS['bg_tertiary']};
                        border-left: 3px solid {COLORS['accent']};
                        border-radius: 6px;
                    }}
                ''')
            else:
                row.setStyleSheet(f'''
                    QFrame {{
                        background-color: transparent;
                        border-radius: 6px;
                    }}
                    QFrame:hover {{
                        background-color: {COLORS['bg_secondary']};
                    }}
                ''')


class BibliotecaView(QWidget):
    """Pantalla principal de biblioteca"""

    def __init__(self, on_play, parent=None):
        super().__init__(parent)
        self.on_play = on_play
        self.stack = parent  # el QStackedWidget
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 25, 30, 25)
        layout.setSpacing(20)

        title = QLabel("📚 Mi Biblioteca")
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        subtitle = QLabel("Tus playlists")
        subtitle.setFont(QFont('Arial', 11))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle)

        playlists_layout = QHBoxLayout()
        playlists_layout.setSpacing(20)
        playlists_layout.setAlignment(Qt.AlignLeft)

        emojis = ["🎸", "🎵", "🔥", "🎧", "⚡"]
        for i, (nombre_playlist, tracks) in enumerate(PLAYLISTS.items()):
            card = self._create_card(emojis[i % len(emojis)], nombre_playlist, tracks)
            playlists_layout.addWidget(card)

        layout.addLayout(playlists_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _create_card(self, emoji: str, nombre: str, tracks: list) -> QFrame:
        card = QFrame()
        card.setFixedSize(200, 240)
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet(f'''
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                background-color: {COLORS['bg_tertiary']};
                border: 1px solid {COLORS['accent']};
            }}
        ''')

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(0, 0, 0, 15)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignCenter)

        # Imagen de portada
        cover_label = QLabel()
        cover_label.setFixedSize(200, 140)
        cover_label.setAlignment(Qt.AlignCenter)
        cover_label.setStyleSheet("border-radius: 12px 12px 0px 0px; background-color: #333;")

        ruta_imagen = PLAYLIST_COVERS.get(nombre)
        if ruta_imagen and os.path.exists(ruta_imagen):
            pixmap = QPixmap(ruta_imagen)
            pixmap = pixmap.scaled(200, 140, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Recortar al centro
            x = (pixmap.width() - 200) // 2
            y = (pixmap.height() - 140) // 2
            pixmap = pixmap.copy(x, y, 200, 140)
            cover_label.setPixmap(pixmap)
        else:
            cover_label.setText(emoji)
            cover_label.setFont(QFont('Arial', 40))

        card_layout.addWidget(cover_label)

        name_label = QLabel(nombre)
        name_label.setFont(QFont('Arial', 11, QFont.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; padding: 0 10px;")
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        card_layout.addWidget(name_label)

        count_label = QLabel(f"{len(tracks)} canciones")
        count_label.setFont(QFont('Arial', 9))
        count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        count_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(count_label)

        card.setLayout(card_layout)
        card.mousePressEvent = lambda e, n=nombre, t=tracks: self._open_playlist(n, t)
        return card

def _open_playlist(self, nombre: str, tracks: list):
    playlist_view = PlaylistView(nombre, tracks, self.on_play, self.stack)
    if self.stack.count() > 3:
        self.stack.removeWidget(self.stack.widget(3))
    self.stack.addWidget(playlist_view)
    self.stack.current_playlist_view = playlist_view  # ← guardar acá
    self.stack.setCurrentIndex(3)

# ─────────────────────────────────────────────
# VENTANA PRINCIPAL
# ─────────────────────────────────────────────

class MusicPlayer(QMainWindow):
    """Aplicación principal del reproductor"""

    search_finished = pyqtSignal(list)
    search_started  = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎵 Reproductor de Música")
        self.setGeometry(100, 100, 1200, 800)
        self.current_track: Optional[dict] = None
        self.is_playing = False
        self.search_results: List[dict] = []
        self.duracion_total = 0
        self.log_area = None  # Se inicializa en setup_ui

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_progress)
        self.update_timer.start(500)

        self.search_started.connect(self._on_search_started)
        self.search_finished.connect(self._on_search_finished)

        self.setup_ui()
        self.apply_styles()
        
        self.playlist_actual = []
        self.playlist_index  = 0
        self.shuffle_on      = False
        
        descargar_playlists(
        on_progress=lambda msg: self.log_area.append(msg)
)

    # ── UI ────────────────────────────────────
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        

        main_layout.addLayout(self._create_player_bar())

        # Layout con sidebar + contenido
        body_layout = QHBoxLayout()
        body_layout.setSpacing(0)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.addWidget(self._create_sidebar(), 0)

        # Stack de pantallas: 0=búsqueda, 1=biblioteca, 2=playlist
        self.content_stack = QStackedWidget()
        
        self.content_stack.current_playlist_view = None  # ← agregá esta línea
        self.content_stack.addWidget(self._create_search_section())                                   # índice 0
        self.content_stack.addWidget(BibliotecaView(self._play_desde_playlist, self.content_stack))  # índice 1
        self.content_stack.addWidget(self._create_config_screen())                                    # índice 2
        body_layout.addWidget(self.content_stack, 1)

        main_layout.addLayout(body_layout, 1)

        # Área de logs
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(120)
        self.log_area.setStyleSheet(f'''
            QTextEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-family: 'Courier New';
                font-size: 9px;
            }}
        ''')
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        central_widget.setLayout(main_layout)

    def _create_player_bar(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)

        # Fila superior: título + controles
        top_row = QHBoxLayout()

        self.track_label = QLabel("🎵 No hay canción seleccionada")
        self.track_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.track_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        top_row.addWidget(self.track_label)
        top_row.addStretch()

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
        # Reemplazá el for de los botones por esto:
        self.shuffle_btn = QPushButton("⇄")
        self.shuffle_btn.setFixedWidth(40)
        self.shuffle_btn.setFont(QFont('Arial', 12))
        self.shuffle_btn.clicked.connect(self._toggle_shuffle)
        self.shuffle_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton:hover {{ color: {COLORS['text_primary']}; }}
        ''')
        control_layout.addWidget(self.shuffle_btn)

        prev_btn = QPushButton("⏮")
        prev_btn.setFixedWidth(40)
        prev_btn.setFont(QFont('Arial', 12))
        prev_btn.clicked.connect(self._prev_track)
        prev_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; }}
        ''')
        control_layout.addWidget(prev_btn)

        for btn_text, callback in [
            ("▶ Play", self._toggle_play),
            ("⏹ Stop", self._stop),
        ]:
            btn = QPushButton(btn_text)
            btn.setFixedWidth(100)
            btn.setFont(QFont('Arial', 9, QFont.Bold))
            btn.clicked.connect(callback)
            btn.setStyleSheet(f'''
                QPushButton {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 6px;
                }}
                QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; }}
            ''')
            control_layout.addWidget(btn)

        next_btn = QPushButton("⏭")
        next_btn.setFixedWidth(40)
        next_btn.setFont(QFont('Arial', 12))
        next_btn.clicked.connect(self._next_track)
        next_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                border-radius: 4px;
                padding: 6px;
            }}
            QPushButton:hover {{ background-color: {COLORS['bg_tertiary']}; }}
        ''')
        control_layout.addWidget(next_btn)
        for btn_text, callback in [
            ("▶ Play", self._toggle_play),
            ("⏹ Stop", self._stop),
        ]:
            btn = QPushButton(btn_text)
            btn.setFixedWidth(100)
            btn.setFont(QFont('Arial', 9, QFont.Bold))
            btn.clicked.connect(callback)
            btn.setStyleSheet(f'''
                QPushButton {{
                    background-color: {COLORS['bg_secondary']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    padding: 6px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['bg_tertiary']};
                }}
            ''')
            
            control_layout.addWidget(btn)
        
        top_row.addLayout(control_layout)
        layout.addLayout(top_row)

        # Barra de progreso
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)

        self.time_label = QLabel("0:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.time_label)
        
        

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMaximum(100)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.setStyleSheet(f'''
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 6px;
                background: {COLORS['bg_secondary']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                width: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }}
        ''')
        progress_layout.addWidget(self.progress_slider)

        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.duration_label)

        layout.addLayout(progress_layout)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {COLORS['border']};")
        layout.addWidget(separator)

        return layout
    def _create_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(200)
        frame.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-right: 1px solid {COLORS['border']};")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)

        logo = QLabel("🎵 ROJIC")
        logo.setFont(QFont('Arial', 16, QFont.Bold))
        logo.setStyleSheet(f"color: {COLORS['accent']}; padding-bottom: 10px;")
        layout.addWidget(logo)

        style = f'''
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_primary']};
                border: none;
                text-align: left;
                padding: 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_tertiary']};
                border-radius: 4px;
            }}
        '''

        buscar_btn = QPushButton("🔍 Búsqueda")
        buscar_btn.setStyleSheet(style)
        buscar_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))
        layout.addWidget(buscar_btn)

        biblioteca_btn = QPushButton("📚 Biblioteca")
        biblioteca_btn.setStyleSheet(style)
        biblioteca_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))
        layout.addWidget(biblioteca_btn)

        cola_btn = QPushButton("📋 Mi Cola")
        cola_btn.setStyleSheet(style)
        layout.addWidget(cola_btn)

        config_btn = QPushButton("⚙️ Configuración")
        config_btn.setStyleSheet(style)
        config_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(2))
        layout.addWidget(config_btn)

        layout.addStretch()
        frame.setLayout(layout)
        return frame
    def _play_desde_playlist(self, track: dict):
        for nombre_playlist, tracks in PLAYLISTS.items():
            for i, t in enumerate(tracks):
                if t['url'] == track['url']:
                    self.playlist_actual = tracks
                    self.playlist_index  = i
                    # Remarcar la fila
                    vista = getattr(self.content_stack, 'current_playlist_view', None)
                    if vista:
                        vista.set_playing(i + 1)
                    break

        self._reproducir_track_playlist(track)

    def _reproducir_track_playlist(self, track: dict):
        ruta = buscar_cancion_playlist(track['nombre'], track['artista'])
        if ruta:
            ruta_final = convertir_a_mp3(ruta)
            self.duracion_total = obtener_duracion(ruta_final)
            if self.duracion_total > 0:
                self.progress_slider.setMaximum(self.duracion_total)
                self.duration_label.setText(self._format_time(self.duracion_total))
            self.track_label.setText(f"▶ {track['nombre']} - {track['artista']}")
            player.reproducir(ruta_final)
            self.is_playing = True
        else:
            track_spotify = {
                'name': track['nombre'],
                'artists': [{'name': track['artista']}],
                'album': '',
                'preview_url': None,
                'external_urls': {'spotify': track['url']},
                'image': None,
            }
            self._on_track_selected(track_spotify)

    def _next_track(self):
        if not hasattr(self, 'playlist_actual') or not self.playlist_actual:
            return
        if self.shuffle_on:
            import random
            self.playlist_index = random.randint(0, len(self.playlist_actual) - 1)
        else:
            self.playlist_index = (self.playlist_index + 1) % len(self.playlist_actual)
        track = self.playlist_actual[self.playlist_index]
        vista = getattr(self.content_stack, 'current_playlist_view', None)
        if vista:
            vista.set_playing(self.playlist_index + 1)
        self._reproducir_track_playlist(track)

    def _prev_track(self):
        if not hasattr(self, 'playlist_actual') or not self.playlist_actual:
            return
        self.playlist_index = (self.playlist_index - 1) % len(self.playlist_actual)
        track = self.playlist_actual[self.playlist_index]
        vista = getattr(self.content_stack, 'current_playlist_view', None)
        if vista:
            vista.set_playing(self.playlist_index + 1)
        self._reproducir_track_playlist(track)

    def _toggle_shuffle(self):
        self.shuffle_on = not self.shuffle_on
        color = COLORS['accent'] if self.shuffle_on else COLORS['text_secondary']
        self.shuffle_btn.setStyleSheet(self.shuffle_btn.styleSheet().replace(
            'color: ' + (COLORS['text_secondary'] if self.shuffle_on else COLORS['accent']),
            'color: ' + color
        ))
    def _create_search_section(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Busca canciones, artistas, álbumes...")
        self.search_input.setFont(QFont('Arial', 11))
        self.search_input.setFixedHeight(40)
        self.search_input.returnPressed.connect(self._search)
        self.search_input.setStyleSheet(f'''
            QLineEdit {{
                background-color: {COLORS['bg_secondary']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 12px;
                selection-background-color: {COLORS['accent']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_secondary']};
            }}
        ''')
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍 Buscar")
        self.search_btn.setFixedSize(120, 40)
        self.search_btn.setFont(QFont('Arial', 10, QFont.Bold))
        self.search_btn.clicked.connect(self._search)
        self.search_btn.setStyleSheet(f'''
            QPushButton {{
                background-color: {COLORS['accent']};
                color: black;
                border: none;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #33CCFF;
            }}
        ''')
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        shortcut = QShortcut(QKeySequence("Return"), self)
        shortcut.activated.connect(self._search)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(10)
        self.results_container.setLayout(self.results_layout)

        scroll = QScrollArea()
        scroll.setWidget(self.results_container)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f'''
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {COLORS['bg_secondary']};
                width: 8px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {COLORS['border']};
                border-radius: 4px;
            }}
        ''')
        layout.addWidget(scroll, 1)

        widget.setLayout(layout)
        return widget

    # ── LÓGICA DE BÚSQUEDA ────────────────────

    def _search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_started.emit()

        def search_thread():
            try:
                results = search_tracks(SPOTIFY_CLIENT, query)
                self.search_results = results
                self.search_finished.emit(results if results else [])
            except Exception as e:
                print(f"Error en búsqueda: {e}")
                self.search_finished.emit([])

        threading.Thread(target=search_thread, daemon=True).start()

    def _on_search_started(self):
        while self.results_layout.count() > 0:
            item = self.results_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        loading = QLabel("🔍 Buscando...")
        loading.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.results_layout.addWidget(loading)

    def _on_search_finished(self, results):
        while self.results_layout.count() > 0:
            item = self.results_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        if not results:
            no_results = QLabel("❌ No se encontraron resultados")
            no_results.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self.results_layout.addWidget(no_results)
        else:
            for track in results:
                item = SearchResultItem(track)
                item.clicked.connect(self._on_track_selected)
                self.results_layout.addWidget(item)

        self.results_layout.addStretch()

    # ── REPRODUCCIÓN ──────────────────────────

    def _on_track_selected(self, track: dict):
        print(f"\n📌 SELECCIONAR CANCIÓN")
        print(f"   Nombre: {track.get('name')}")
        print(f"   Artista: {', '.join([a.get('name', '') for a in track.get('artists', [])])}")

        self.current_track = track
        self.track_label.setText(
            f"▶ {track.get('name')} - "
            f"{', '.join([a.get('name', '') for a in track.get('artists', [])])}"
        )

        preview_url = track.get('preview_url')
        print(f"   Preview URL: {preview_url}")

        if preview_url:
            print(f"   ✅ Preview disponible")
            preview_path = os.path.join(tempfile.gettempdir(), "preview.mp3")
            try:
                response = requests.get(preview_url, timeout=10)
                if response.status_code != 200:
                    print(f"   ❌ Error HTTP {response.status_code}")
                    return
                with open(preview_path, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Preview descargado ({len(response.content)} bytes)")

                self.duracion_total = 30
                self.progress_slider.setMaximum(self.duracion_total)
                self.duration_label.setText(self._format_time(self.duracion_total))

                player.reproducir(preview_path)
                self.is_playing = True
                print(f"   ✅ Reproducción iniciada")

            except requests.exceptions.Timeout:
                print(f"   ❌ TIMEOUT al descargar preview")
            except Exception as e:
                print(f"   ❌ ERROR: {type(e).__name__}: {e}")

        else:
            print(f"   ❌ NO HAY PREVIEW URL")
            track_name = track.get('name', '')
            locales = buscar_canciones_locales(track_name)

            if locales:
                ruta = locales[0]['path']
                ruta_final = convertir_a_mp3(ruta)

                self.duracion_total = obtener_duracion(ruta_final)
                if self.duracion_total > 0:
                    self.progress_slider.setMaximum(self.duracion_total)
                    self.duration_label.setText(self._format_time(self.duracion_total))

                player.reproducir(ruta_final)
                self.is_playing = True
                print(f"   ✅ Reproducción iniciada desde local")

            else:
                print(f"   ⬇️ No encontrada localmente, intentando descargar...")

                def descargar_y_reproducir():
                    try:
                        ruta_descargada = descargar_desde_spotify(track)
                        if ruta_descargada:
                            for root, dirs, files in os.walk(ruta_descargada):
                                for archivo in files:
                                    if archivo.lower().endswith(('.mp3', '.wav', '.webm')):
                                        ruta_final = convertir_a_mp3(os.path.join(root, archivo))
                                        self.duracion_total = obtener_duracion(ruta_final)
                                        if self.duracion_total > 0:
                                            self.progress_slider.setMaximum(self.duracion_total)
                                            self.duration_label.setText(self._format_time(self.duracion_total))
                                        player.reproducir(ruta_final)
                                        self.is_playing = True
                                        print(f"   ✅ Reproducción iniciada")
                                        return
                            print(f"   ❌ No se encontraron archivos en carpeta descargada")
                        else:
                            print(f"   ❌ No se pudo descargar: {track['external_urls']['spotify']}")
                    except Exception as e:
                        print(f"   ❌ Error en descarga: {type(e).__name__}: {e}")
                        import traceback
                        traceback.print_exc()

                threading.Thread(target=descargar_y_reproducir, daemon=True).start()
                print(f"   🧵 Thread de descarga iniciado")
                
        print(f"   🔗 URL Spotify: {track['external_urls']['spotify']}")

    def _toggle_play(self):
        if self.is_playing:
            player.pausar()
        else:
            player.reanudar()
        self.is_playing = not self.is_playing

    def _stop(self):
        player.stop()
        self.is_playing = False

    def _on_slider_moved(self, position):
        if self.duracion_total > 0:
            player.set_pos(position)

    def _update_progress(self):
        if self.is_playing:
            pos = player.get_pos()
            if pos >= 0:
                pos_seconds = pos / 1000
                self.progress_slider.setValue(int(pos_seconds))
                self.time_label.setText(self._format_time(pos_seconds))

    @staticmethod
    def _format_time(seconds: float) -> str:
        if not seconds or seconds < 0:
            return "0:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    def apply_styles(self):
        self.setStyleSheet(f'''
            QMainWindow {{
                background-color: {COLORS['bg_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
            }}
            QLineEdit {{
                color: {COLORS['text_primary']};
                background-color: {COLORS['bg_secondary']};
            }}
        ''')
    def _create_config_screen(self) -> QWidget:
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        emoji = QLabel("☠️")
        emoji.setFont(QFont('Arial', 60))
        emoji.setAlignment(Qt.AlignCenter)
        layout.addWidget(emoji)

        msg = QLabel("Todos los derechos claramente robados xd")
        msg.setFont(QFont('Arial', 18, QFont.Bold))
        msg.setStyleSheet(f"color: {COLORS['text_primary']};")
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)

        sub = QLabel("© 2026 ROJIC Music — ningún derecho reservado")
        sub.setFont(QFont('Arial', 11))
        sub.setStyleSheet(f"color: {COLORS['text_secondary']};")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)

        widget.setLayout(layout)
        return widget


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("🎵 Reproductor de Música")
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
