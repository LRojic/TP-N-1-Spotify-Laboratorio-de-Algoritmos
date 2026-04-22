🎵 Reproductor de Música — Python Edition

Trabajo Práctico N°1 — Laboratorio de Algoritmos

Aplicación de escritorio desarrollada en Python + PyQt5 con interfaz moderna tipo Apple Music. Permite buscar música en Spotify y reproducir previews con controles completos.

✨ Funcionalidades
🔍 Búsqueda de canciones, artistas y álbumes (Spotify)
▶️ Reproducción de previews (30s)
🎛️ Controles: Play, Pause, Stop, Siguiente, Anterior
📊 Barra de progreso interactiva
🎨 Interfaz moderna (modo oscuro)
⚙️ Backend con Spotipy + pygame
🏗️ Estructura
.
├── main.py
├── spotify_api.py
├── player.py
├── requirements.txt
└── downloads/
🚀 Instalación
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

Crear .env:

SPOTIFY_CLIENT_ID=tu_id
SPOTIFY_CLIENT_SECRET=tu_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

Ejecutar:

python main.py
🎮 Uso
Buscar (ej: Arctic Monkeys)
Seleccionar canción
▶️ Play
🛠️ Tecnologías

PyQt5 · Spotipy · pygame · Pillow · requests

📄 Licencia

Uso educativo