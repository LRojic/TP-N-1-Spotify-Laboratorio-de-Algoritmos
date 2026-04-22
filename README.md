# 🎵 Reproductor de Música Profesional - Python Edition

**Trabajo Práctico N°1 - Laboratorio de Algoritmos**

Reproductor de música moderno y elegante desarrollado **100% en Python** con interfaz gráfica tipo Apple Music usando PyQt5. Integra búsqueda en Spotify, reproducción de audio, y gestión de cola.

## 🎯 Características Principales

✅ **Búsqueda en Spotify**
- Búsqueda en tiempo real de canciones, artistas, álbumes
- Visualización de carátulas, información de track
- 8 resultados por búsqueda

✅ **Reproducción de Audio**
- Reproducción de previews de 30 segundos desde Spotify
- Controles: Play, Pause, Stop, Siguiente, Anterior
- Barra de progreso interactiva
- Indicador de tiempo actual/duración

✅ **Interfaz Moderna**
- Diseño tipo Apple Music oscuro y elegante
- Tema personalizado con colores profesionales
- Responsive y fluido
- Botones con hover effects

✅ **Backend Python**
- Integración con Spotify Web API (spotipy)
- Reproducción con pygame
- Gestión de descargas opcional con YouTube

## 🏗️ Arquitectura

### Backend Python
```
.
├── main.py                 # Aplicación principal (PyQt5)
├── spotify_api.py          # Servicios de Spotify
├── player.py               # Motor de reproducción (pygame)
├── requirements.txt        # Dependencias Python
└── downloads/              # Canciones descargadas (opcional)
```

### Tecnologías
- **PyQt5**: Interfaz gráfica moderna
- **Spotipy**: API de Spotify
- **pygame**: Motor de audio
- **Pillow**: Procesamiento de imágenes
- **requests**: HTTP cliente

## 🚀 Instalación Rápida

### 1️⃣ Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 2️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3️⃣ Configurar Spotify API

1. Ir a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Crear una nueva aplicación
3. Copiar **Client ID** y **Client Secret**
4. Crear archivo `.env` en la raíz:

```env
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### 4️⃣ Ejecutar la aplicación
```bash
python main.py
```

## 🎨 Interfaz

### Estructura Visual
```
┌─────────────────────────────────────────────┐
│  🎵 Track Name - Artist                     │
│  ▶ Play ⏸ Pause ⏹ Stop ⏭ Skip  (Controles)│
│  |━━━━━◯━━━━━━| 0:45 / 3:20  (Progreso)   │
├──────────────┬──────────────────────────────┤
│   SIDEBAR    │   BÚSQUEDA Y RESULTADOS     │
│              │   🔍 [buscador] [Buscar]    │
│ 🏠 Home      │                              │
│ 🔍 Buscar    │   ┌──────────────────────┐  │
│ 📋 Mi Cola   │   │ [Album] Canción      │  │
│ ⚙️ Config    │   │ Artista - Album      │  │
│              │   │        ▶ Play        │  │
│              │   └──────────────────────┘  │
│              │                              │
│              │   ... más resultados ...    │
└──────────────┴──────────────────────────────┘
```

## 🎮 Controles

| Botón | Acción |
|-------|--------|
| **▶ Play** | Reproducir o reanudar |
| **⏸ Pause** | Pausar reproducción |
| **⏹ Stop** | Detener reproducción |
| **⏭ Siguiente** | Siguiente canción |
| **⏮ Anterior** | Canción anterior |
| **Slider** | Saltar a posición |

## 📝 Módulos del Backend

### `spotify_api.py`
Gestiona la conexión con Spotify:
```python
from spotify_api import get_spotify_client, search_tracks

sp = get_spotify_client()
results = search_tracks(sp, "Arctic Monkeys")
```

### `player.py`
Controla la reproducción de audio:
```python
from player import reproducir, pausar, reanudar, stop, get_pos, set_pos

reproducir("cancion.mp3")
pausar()
reanudar()
set_pos(45)  # Saltar a 45 segundos
pos = get_pos()  # Obtener posición actual
```

### `main.py`
Aplicación principal con PyQt5:
```python
from main import MusicPlayer

# Se ejecuta con: python main.py
```

## ⚙️ Configuración Avanzada

### Variables de entorno (.env)
```env
# Spotify API
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

### Personalizacion de Colores (main.py)
```python
COLORS = {
    'bg_primary': '#121212',      # Fondo
    'accent': '#00BFFF',          # Azul eléctrico
    'text_primary': '#FFFFFF',    # Texto
    # ... más colores
}
```

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'PyQt5'"
```bash
pip install PyQt5
```

### Error: "Spotify credentials invalid"
- Verifica Client ID y Secret en `.env`
- Recrea las credenciales en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

### Error: "No audio device found"
- Verifica que tu sistema tenga un dispositivo de audio activo
- Instala/actualiza audio drivers

### La búsqueda es lenta
- Spotify API tiene rate limiting
- Intenta de nuevo en unos segundos

## 🔮 Extensiones Futuras

- [ ] Playlist personalizadas
- [ ] Historial de reproducción
- [ ] Descargas en background
- [ ] Sincronización multidevice
- [ ] Ecualizador de audio
- [ ] Modo dark/light
- [ ] Integración con YouTube

## 📦 Dependencias

```
PyQt5>=5.15.0
spotipy>=2.19.0
pygame>=2.1.0
Pillow>=9.0.0
python-dotenv>=0.19.0
requests>=2.26.0
moviepy>=1.0.3
imageio-ffmpeg>=0.4.5
yt-dlp>=2022.0.0
```

## 📄 Licencia

Uso educativo - Trabajo Práctico

## 🤝 Autor

Desarrollado como ejercicio de integración de APIs y desarrollo GUI en Python.

---

**🎵 ¡Disfruta tu música!** 🎉
## 🚀 INICIO RÁPIDO

### Requisitos
- Python 3.8+
- Spotify Developer Account (gratis)

### 5 Minutos para empezar:

**1️⃣ Instalar dependencias:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2️⃣ Configurar Spotify:**
```
1. Ir a: https://developer.spotify.com/dashboard
2. Crear App → Copiar Client ID y Secret
3. Crear .env con:
```
```env
SPOTIFY_CLIENT_ID=tu_id
SPOTIFY_CLIENT_SECRET=tu_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

**3️⃣ Ejecutar:**
```bash
# Windows
run.bat

# Linux/Mac
bash run.sh

# O directamente
python main.py
```

**¡Listo! 🎵**

---

## 🎯 Primera prueba:
1. Escribe "Arctic Monkeys" en el buscador
2. Hace click en "Buscar"
3. Selecciona una canción
4. ▶ Play

¡A disfrutar! 🎧
