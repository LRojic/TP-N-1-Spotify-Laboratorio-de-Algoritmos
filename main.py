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

# Configuración
load_dotenv()
SPOTIFY_CLIENT = get_spotify_client()
CARPETA_DESCARGAS = "downloads"
Path(CARPETA_DESCARGAS).mkdir(exist_ok=True)

# Colores (tema oscuro Apple Music)
COLORS = {
    'bg_primary': '#121212',      # Fondo principal
    'bg_secondary': '#1E1E1E',    # Fondo secundario
    'bg_tertiary': '#2E2E2E',     # Fondo terciario
    'accent': '#00BFFF',          # Azul eléctrico
    'text_primary': '#FFFFFF',    # Texto principal
    'text_secondary': '#B3B3B3',  # Texto secundario
    'border': '#282828',          # Bordes
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

def descargar_desde_spotify(track):
    """Descarga una canción desde Spotify usando spotify_dl"""
    print(f"   ⬇️ Descargando desde Spotify...")
    try:
        # Usar la URL de Spotify para descargar
        url = track['external_urls']['spotify']
        print(f"   📍 URL: {url}")
        
        # Crear carpeta con nombre del track
        nombre_track = track.get('name', 'cancion').replace('/', '_').replace('\\', '_')
        carpeta_descarga = os.path.join(CARPETA_DESCARGAS, nombre_track)
        os.makedirs(carpeta_descarga, exist_ok=True)
        
        # Usar libs.spotify_downloader
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
        
        # Nombre canción
        name_label = QLabel(self.track.get('name', 'Unknown'))
        name_label.setFont(QFont('Arial', 11, QFont.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        info_layout.addWidget(name_label)
        
        # Artista
        artists = ', '.join([a.get('name', '') for a in self.track.get('artists', [])])
        artist_label = QLabel(artists)
        artist_label.setFont(QFont('Arial', 9))
        artist_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(artist_label)
        
        # Álbum
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

class MusicPlayer(QMainWindow):
    """Aplicación principal del reproductor"""
    
    search_finished = pyqtSignal(list)
    search_started = pyqtSignal()
    
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
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        top_layout = self._create_player_bar()
        main_layout.addLayout(top_layout)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        sidebar = self._create_sidebar()
        content_layout.addWidget(sidebar, 0)
        main_content = self._create_search_section()
        content_layout.addWidget(main_content, 1)
        main_layout.addLayout(content_layout, 1)
        
        # Área de logs en la parte inferior
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(150)
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
            
        top_row = QHBoxLayout()
        self.track_label = QLabel("🎵 No hay canción seleccionada")
        self.track_label.setFont(QFont('Arial', 12, QFont.Bold))
        self.track_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        top_row.addWidget(self.track_label)
        top_row.addStretch()

        self.time_label = QLabel("0:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.time_label)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)
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
        
        progress_layout = QHBoxLayout()
        # Tiempo actual
        self.time_label = QLabel("0:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.time_label)

        # Slider
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMaximum(100)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        progress_layout.addWidget(self.progress_slider)

        # Duración total
        self.duration_label = QLabel("0:00")
        self.duration_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.duration_label)
        progress_layout.setSpacing(10)
        
        # Label único para tiempo actual / duración total
        self.progress_label = QLabel("0:00 / 0:00")
        self.progress_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_slider = QSlider(Qt.Horizontal)
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
        self.progress_slider.setMaximum(100)
        progress_layout.addWidget(self.progress_slider)
        
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
        layout.setSpacing(15)
        
        logo = QLabel("🎵 MUSIC")
        logo.setFont(QFont('Arial', 16, QFont.Bold))
        logo.setStyleSheet(f"color: {COLORS['accent']};")
        layout.addWidget(logo)
        
        for item in ["🏠 Home", "🔍 Buscar", "📋 Mi Cola", "⚙️ Configuración"]:
            btn = QPushButton(item)
            btn.setStyleSheet(f'''
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
            ''')
            layout.addWidget(btn)
        
        layout.addStretch()
        frame.setLayout(layout)
        return frame
    
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
        self.results_container.setLayout(self.results_layout)
        layout.addWidget(scroll, 1)
        widget.setLayout(layout)
        return widget
    
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
        
        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()
    
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
    
    def _on_track_selected(self, track: dict):
        print(f"\n📌 SELECCIONAR CANCIÓN")
        print(f"   Nome: {track.get('name')}")
        print(f"   Artista: {', '.join([a.get('name', '') for a in track.get('artists', [])])}")
        
        self.current_track = track
        self.track_label.setText(f"▶ {track.get('name')} - {', '.join([a.get('name', '') for a in track.get('artists', [])])}")
        
        preview_url = track.get('preview_url')
        print(f"   Preview URL: {preview_url}")
        
        # ────────── SI HAY PREVIEW (30 SEGUNDOS) ──────────
        if preview_url:
            print(f"   ✅ Preview disponible")
            preview_path = os.path.join(tempfile.gettempdir(), "preview.mp3")
            print(f"   📥 Descargando a: {preview_path}")
            
            try:
                response = requests.get(preview_url, timeout=10)
                print(f"   Status: {response.status_code}")
                print(f"   Tamaño: {len(response.content)} bytes")
                
                if response.status_code != 200:
                    print(f"   ❌ Error HTTP {response.status_code}")
                    return
                
                with open(preview_path, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Preview descargado")
                
                # Set duration for preview (30 seconds)
                self.duracion_total = 30
                self.progress_slider.setMaximum(self.duracion_total)
                self.duration_label.setText(self._format_time(self.duracion_total))
                
                print(f"   ▶️ Reproduciendo preview...")
                player.reproducir(preview_path)
                self.is_playing = True
                print(f"   ✅ Reproducción iniciada")
                
            except requests.exceptions.Timeout:
                print(f"   ❌ TIMEOUT al descargar preview")
            except Exception as e:
                print(f"   ❌ ERROR: {type(e).__name__}: {e}")
        
        # ────────── SIN PREVIEW: BUSCAR LOCALMENTE ──────────
        else:
            print(f"   ❌ NO HAY PREVIEW URL")
            track_name = track.get('name', '')
            
            # Buscar localmente
            locales = buscar_canciones_locales(track_name)
            
            if locales:
                print(f"   ✅ Canción encontrada localmente")
                ruta = locales[0]['path']
                print(f"   📂 Ruta: {ruta}")
                
                # Convertir a MP3 si es necesario
                ruta_final = convertir_a_mp3(ruta)
                
                # Set duration
                self.duracion_total = obtener_duracion(ruta_final)
                if self.duracion_total > 0:
                    self.progress_slider.setMaximum(self.duracion_total)
                    self.duration_label.setText(self._format_time(self.duracion_total))
                
                # Reproducir
                print(f"   ▶️ Reproduciendo desde local...")
                player.reproducir(ruta_final)
                self.is_playing = True
                print(f"   ✅ Reproducción iniciada")
                
            else:
                print(f"   ⬇️ No encontrada localmente, intentando descargar...")
                
                def descargar_y_reproducir():
                    try:
                        ruta_descargada = descargar_desde_spotify(track)
                        
                        if ruta_descargada:
                            # Buscar archivo descargado
                            for root, dirs, files in os.walk(ruta_descargada):
                                for archivo in files:
                                    if archivo.lower().endswith(('.mp3', '.wav', '.webm')):
                                        ruta_archivo = os.path.join(root, archivo)
                                        ruta_final = convertir_a_mp3(ruta_archivo)
                                        
                                        # Set duration
                                        self.duracion_total = obtener_duracion(ruta_final)
                                        if self.duracion_total > 0:
                                            self.progress_slider.setMaximum(self.duracion_total)
                                            self.duration_label.setText(self._format_time(self.duracion_total))
                                        
                                        print(f"   ▶️ Reproduciendo descargada...")
                                        player.reproducir(ruta_final)
                                        self.is_playing = True
                                        print(f"   ✅ Reproducción iniciada")
                                        return
                            
                            print(f"   ❌ No se encontraron archivos en carpeta descargada")
                        else:
                            print(f"   ❌ No se pudo descargar, abre manualmente:")
                            print(f"      {track['external_urls']['spotify']}")
                            
                    except Exception as e:
                        print(f"   ❌ Error en descarga: {type(e).__name__}: {e}")
                        import traceback
                        traceback.print_exc()
                
                thread = threading.Thread(target=descargar_y_reproducir, daemon=True)
                thread.start()
                print(f"   🧵 Thread de descarga iniciado")
    
    def _toggle_play(self):
        if self.is_playing:
            player.pausar()
        else:
            player.reanudar()
        self.is_playing = not self.is_playing
    
    def _stop(self):
        player.stop()
        self.is_playing = False
    def _update_progress(self):
        if self.is_playing:
            pos = player.get_pos()

            if pos >= 0:
                pos_seconds = pos / 1000  # 👈 convertir ms → segundos

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

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("🎵 Reproductor de Música")
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
