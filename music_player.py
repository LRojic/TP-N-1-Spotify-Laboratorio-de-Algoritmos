"""
🎵 Reproductor de Música - Ventana Principal
Contiene la clase MusicPlayer y componentes relacionados
"""

# ===== STANDARD LIB =====
import sys
import os
import threading
import tempfile
from typing import Optional, List

# ===== THIRD PARTY =====
import requests

# ===== PYQT5 =====
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSlider, QScrollArea, QFrame,
    QTextEdit, QShortcut, QStackedWidget, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QKeySequence

# ===== LOCAL =====
import player
from spotify_api import get_spotify_client, search_tracks
from libs.spotify_downloader import download_track
from main import (
    COLORS, PLAYLISTS, PLAYLIST_COVERS, CARPETA_DESCARGAS,
    buscar_canciones_locales, convertir_a_mp3, descargar_desde_spotify,
    obtener_duracion, buscar_cancion_playlist, SPOTIFY_CLIENT
)


# ─────────────────────────────────────────────
# WIDGETS RELACIONADOS CON MUSICPLAYER
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

        self.emojis = ["🎸", "🎵", "🔥", "🎧", "⚡"]
        self.playlists_layout = playlists_layout
        self._build_playlists()

        layout.addLayout(playlists_layout)
        layout.addStretch()
        self.setLayout(layout)

    def _create_card(self, emoji: str, nombre: str, tracks: list) -> QFrame:
        card = QFrame()
        card.setFixedSize(200, 300)
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
        cover_label.setFixedSize(200, 200)
        cover_label.setAlignment(Qt.AlignCenter)
        cover_label.setStyleSheet("border-radius: 12px 12px 0px 0px; background-color: #333;")

        ruta_imagen = PLAYLIST_COVERS.get(nombre)
        if ruta_imagen and os.path.exists(ruta_imagen):
            pixmap = QPixmap(ruta_imagen)
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Recortar al centro
            x = (pixmap.width() - 200) // 2
            y = (pixmap.height() - 200) // 2
            pixmap = pixmap.copy(x, y, 200, 200)
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
    
    def _build_playlists(self):
        while self.playlists_layout.count():
            item = self.playlists_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for i, (nombre_playlist, tracks) in enumerate(PLAYLISTS.items()):
            card = self._create_card(self.emojis[i % len(self.emojis)], nombre_playlist, tracks)
            self.playlists_layout.addWidget(card)

    def reload_playlists(self):
        self._build_playlists()

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
    log_signal      = pyqtSignal(str)

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
        self.local_playlist_dirs = {}
        
        from main import descargar_playlists
        descargar_playlists(
            on_progress=lambda msg: self.log_area.append(msg)
        )
        player.set_on_finish(self._on_track_finished)
        
        # Inicializar volumen (80% por defecto)
        player.set_volume(0.8)

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
        self.biblioteca_view = BibliotecaView(self._play_desde_playlist, self.content_stack)
        self.content_stack.addWidget(self.biblioteca_view)                                            # índice 1
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

        self.play_pause_btn = QPushButton("⏸ Pausar")
        self.play_pause_btn.setFixedWidth(100)
        self.play_pause_btn.setFont(QFont('Arial', 9, QFont.Bold))
        self.play_pause_btn.clicked.connect(self._toggle_play)
        self.play_pause_btn.setStyleSheet(f'''
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
        control_layout.addWidget(self.play_pause_btn)

        stop_btn = QPushButton("⏹ Stop")
        stop_btn.setFixedWidth(100)
        stop_btn.setFont(QFont('Arial', 9, QFont.Bold))
        stop_btn.clicked.connect(self._stop)
        stop_btn.setStyleSheet(f'''
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
        control_layout.addWidget(stop_btn)

        top_row.addLayout(control_layout)
        layout.addLayout(top_row)

        # Barra de progreso
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)

        self.time_label = QLabel("0:00")
        self.time_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        progress_layout.addWidget(self.time_label)
        
        

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMaximum(0)  
        self.progress_slider.sliderPressed.connect(lambda: self.progress_slider.blockSignals(False))
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
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

        # Separador
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        progress_layout.addWidget(sep)

        # Control de volumen
        vol_icon = QLabel("🔊")
        vol_icon.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        progress_layout.addWidget(vol_icon)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setStyleSheet(f'''
            QSlider::groove:horizontal {{
                border: 1px solid {COLORS['border']};
                height: 4px;
                background: {COLORS['bg_secondary']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent']};
                width: 10px;
                margin: -3px 0;
                border-radius: 5px;
            }}
        ''')
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        progress_layout.addWidget(self.volume_slider)

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

        abrir_btn = QPushButton("📂 Abrir Archivo")
        abrir_btn.setStyleSheet(style)
        abrir_btn.clicked.connect(self._abrir_archivo_local)
        layout.addWidget(abrir_btn)

        carpeta_btn = QPushButton("📁 Abrir Carpeta")
        carpeta_btn.setStyleSheet(style)
        carpeta_btn.clicked.connect(self._abrir_carpeta_local)
        layout.addWidget(carpeta_btn)

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
                if (track.get('url') and t.get('url') == track.get('url')) or (track.get('path') and t.get('path') == track.get('path')):
                    self.playlist_actual = tracks
                    self.playlist_index  = i
                    # Remarcar la fila
                    vista = getattr(self.content_stack, 'current_playlist_view', None)
                    if vista:
                        vista.set_playing(i + 1)
                    break
            else:
                continue
            break

        self._reproducir_track_playlist(track)

    def _reproducir_track_playlist(self, track: dict):
        ruta = track.get('path') or buscar_cancion_playlist(track['nombre'], track['artista'])
        if ruta and os.path.exists(ruta):
            ruta_final = convertir_a_mp3(ruta)
            self.duracion_total = obtener_duracion(ruta_final)
            self.progress_slider.setMaximum(max(self.duracion_total, 1))  # mínimo 1 para evitar division por cero
            self.duration_label.setText(self._format_time(self.duracion_total))
            self.track_label.setText(f"▶ {track.get('nombre', 'Desconocido')} - {track.get('artista', 'Local')}")
            player.reproducir(ruta_final)
            self.is_playing = True
            return

        if track.get('url'):
            track_spotify = {
                'name': track['nombre'],
                'artists': [{'name': track['artista']}],
                'album': '',
                'preview_url': None,
                'external_urls': {'spotify': track['url']},
                'image': None,
            }
            self._on_track_selected(track_spotify)
        else:
            self.log_area.append(f"❌ No se encontró ruta local para: {track.get('nombre', 'Desconocido')}")

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

    def _on_track_finished(self):
        if self.playlist_actual:
            self._next_track()
        else:
            self.is_playing = False
            self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(0)
            self.progress_slider.blockSignals(False)
            self.time_label.setText("0:00")

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
                self.log_area.append(f"▶️ Reproduciendo: {track.get('name')} - {', '.join([a.get('name','') for a in track.get('artists',[])])}")
                print(f"   ✅ Reproducción iniciada")

            except requests.exceptions.Timeout:
                print(f"   ❌ TIMEOUT al descargar preview")
            except Exception as e:
                print(f"   ❌ ERROR: {type(e).__name__}: {e}")

        else:
            track_name = track.get('name', '')
            locales = buscar_canciones_locales(track_name)

            if locales:
                ruta = locales[0]['path']
                ruta_final = convertir_a_mp3(ruta)

                self.duracion_total = obtener_duracion(ruta_final)
                self.progress_slider.setMaximum(max(self.duracion_total, 1))  # mínimo 1 para evitar division por cero
                self.duration_label.setText(self._format_time(self.duracion_total))

                player.reproducir(ruta_final)
                self.is_playing = True
                self.log_area.append(f"▶️ Reproduciendo (local): {track.get('name')} - {', '.join([a.get('name','') for a in track.get('artists',[])])}")
                print(f"   ✅ Reproducción iniciada desde local")

            else:
                print(f"   ⬇️ No encontrada localmente, intentando descargar...")

                def descargar_y_reproducir():
                    nombre_display = (
                        f"{track.get('name')} - "
                        f"{', '.join([a.get('name','') for a in track.get('artists', [])])}"
                    )
                    self.log_signal.emit(f"⬇️ Descargando: {nombre_display}...")
                    try:
                        ruta_descargada = descargar_desde_spotify(track)
                        if ruta_descargada:
                            for root, dirs, files in os.walk(ruta_descargada):
                                for archivo in files:
                                    if archivo.lower().endswith(('.mp3', '.wav', '.webm')):
                                        ruta_final = convertir_a_mp3(os.path.join(root, archivo))
                                        self.duracion_total = obtener_duracion(ruta_final)
                                        self.progress_slider.setMaximum(max(self.duracion_total, 1))  # mínimo 1 para evitar division por cero
                                        self.duration_label.setText(self._format_time(self.duracion_total))
                                        player.reproducir(ruta_final)
                                        self.is_playing = True
                                        self.log_signal.emit(f"✅ Descargada y reproduciendo: {nombre_display}")
                                        print(f"   ✅ Reproducción iniciada")
                                        return
                            self.log_signal.emit(f"❌ No se encontró archivo: {nombre_display}")
                            print(f"   ❌ No se encontraron archivos en carpeta descargada")
                        else:
                            self.log_signal.emit(f"❌ No se pudo descargar: {nombre_display}")
                            print(f"   ❌ No se pudo descargar: {track['external_urls']['spotify']}")
                    except Exception as e:
                        self.log_signal.emit(f"❌ Error descargando {nombre_display}: {e}")
                        print(f"   ❌ Error en descarga: {type(e).__name__}: {e}")
                        import traceback
                        traceback.print_exc()

                threading.Thread(target=descargar_y_reproducir, daemon=True).start()
                print(f"   🧵 Thread de descarga iniciado")
                
        print(f"   🔗 URL Spotify: {track['external_urls']['spotify']}")

    def _toggle_play(self):
        if self.is_playing:
            player.pausar()
            self.play_pause_btn.setText("▶ Despausar")
        else:
            player.reanudar()
            self.play_pause_btn.setText("⏸ Pausar")
        self.is_playing = not self.is_playing

    def _stop(self):
        player.stop()
        self.is_playing = False
        if hasattr(self, 'play_pause_btn'):
            self.play_pause_btn.setText("▶ Play")

    def _on_slider_released(self):
        """Se ejecuta cuando el usuario suelta el slider"""
        if self.duracion_total > 0:
            player.set_pos(float(self.progress_slider.value()))

    def _on_slider_moved(self, position):
        """El usuario arrastró el slider — saltar a esa posición."""
        if self.duracion_total > 0:
            player.set_pos(float(position))

    def _update_progress(self):
        if not self.is_playing:
            return
        pos = player.get_pos()
        if pos < 0:
            return
        self.progress_slider.blockSignals(True)
        self.progress_slider.setValue(int(pos))
        self.progress_slider.blockSignals(False)
        self.time_label.setText(self._format_time(pos))          # ← solo time_label (izquierda)
        # duration_label NO se toca acá, ya fue seteado al cargar

    def _on_volume_changed(self, value: int):
        """Control de volumen - ajusta el volumen de pygame"""
        player.set_volume(value / 100.0)

    def _abrir_archivo_local(self):
        """Abre un diálogo para seleccionar archivos de audio locales"""
        archivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar archivos de audio",
            "",
            "Archivos de audio (*.mp3 *.wav *.webm *.m4a *.flac *.ogg);;Todos los archivos (*)"
        )
        
        if archivos:
            for ruta in archivos:
                self._reproducir_archivo_local(ruta)

    def _abrir_carpeta_local(self):
        """Abre un diálogo para seleccionar una carpeta de audio y crear una playlist."""
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de audio",
            ""
        )
        if not carpeta:
            return

        archivos = []
        for root, _, files in os.walk(carpeta):
            for archivo in sorted(files):
                if archivo.lower().endswith(('.mp3', '.wav', '.webm', '.m4a', '.flac', '.ogg')):
                    archivos.append(os.path.join(root, archivo))

        if not archivos:
            self.log_area.append(f"❌ No hay archivos de audio en: {carpeta}")
            return

        self._crear_playlist_desde_carpeta(carpeta, archivos)
        self._reproducir_archivo_local(archivos[0], crear_playlist=False)

    def _crear_playlist_desde_carpeta(self, carpeta: str, archivos: list):
        carpeta = os.path.abspath(carpeta)
        if carpeta in self.local_playlist_dirs:
            nombre_playlist = self.local_playlist_dirs[carpeta]
            tracks = []
            for ruta in archivos:
                nombre_archivo = os.path.splitext(os.path.basename(ruta))[0]
                tracks.append({
                    'nombre': nombre_archivo,
                    'artista': 'Local',
                    'path': ruta,
                })
            PLAYLISTS[nombre_playlist] = tracks
            self.log_area.append(f"✅ Playlist local actualizada: {nombre_playlist} ({len(tracks)} canciones)")
            self._refresh_biblioteca()
            return

        nombre_carpeta = os.path.basename(carpeta) or carpeta
        nombre_playlist = f"📁 {nombre_carpeta}"
        original_name = nombre_playlist
        contador = 1
        while nombre_playlist in PLAYLISTS:
            contador += 1
            nombre_playlist = f"{original_name} ({contador})"

        tracks = []
        for ruta in archivos:
            nombre_archivo = os.path.splitext(os.path.basename(ruta))[0]
            tracks.append({
                'nombre': nombre_archivo,
                'artista': 'Local',
                'path': ruta,
            })

        PLAYLISTS[nombre_playlist] = tracks
        self.local_playlist_dirs[carpeta] = nombre_playlist
        self.log_area.append(f"✅ Playlist local creada: {nombre_playlist} ({len(tracks)} canciones)")
        self._refresh_biblioteca()

    def _refresh_biblioteca(self):
        if hasattr(self, 'biblioteca_view') and self.biblioteca_view:
            self.biblioteca_view.reload_playlists()

    def _reproducir_archivo_local(self, ruta: str, crear_playlist: bool = True):
        """Reproduce un archivo de audio local"""
        if not os.path.exists(ruta):
            self.log_area.append(f"❌ Archivo no encontrado: {ruta}")
            return

        if crear_playlist:
            carpeta = os.path.dirname(ruta)
            if carpeta and carpeta not in self.local_playlist_dirs:
                archivos = []
                for root, _, files in os.walk(carpeta):
                    for archivo in sorted(files):
                        if archivo.lower().endswith(('.mp3', '.wav', '.webm', '.m4a', '.flac', '.ogg')):
                            archivos.append(os.path.join(root, archivo))
                if archivos:
                    self._crear_playlist_desde_carpeta(carpeta, archivos)

        # Convertir a MP3 si es necesario
        ruta_final = convertir_a_mp3(ruta)
        
        # Obtener duración
        self.duracion_total = obtener_duracion(ruta_final)
        self.progress_slider.setMaximum(max(self.duracion_total, 1))
        self.duration_label.setText(self._format_time(self.duracion_total))
        
        # Nombre del archivo sin extensión
        nombre_archivo = os.path.splitext(os.path.basename(ruta))[0]
        
        # Actualizar UI
        self.track_label.setText(f"▶ {nombre_archivo} (Local)")
        self.current_track = {'name': nombre_archivo, 'local': True, 'path': ruta_final}
        
        # Reproducir
        player.reproducir(ruta_final)
        self.is_playing = True
        
        self.log_area.append(f"▶️ Reproduciendo: {nombre_archivo}")

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