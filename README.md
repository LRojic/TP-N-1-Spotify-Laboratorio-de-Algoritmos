# Trabajo-practico-N-1---Laboratorio-de-Algoritmos
Reproductor de Música – Trabajo Práctico N°1

Descripción del proyecto


Este proyecto es un reproductor de música desarrollado en Python con Tkinter para la interfaz y Spotipy para interactuar con la API de Spotify. Permite buscar canciones, ver nombre de artista y álbum, y reproducir previews de 30 segundos de cada track.

Funcionalidades implementadas
Búsqueda de canciones por nombre o artista usando la API de Spotify
Visualización de los resultados en una lista
Reproducción de previews de las canciones (30 segundos)
Interfaz gráfica simple con Tkinter
Cómo se inició la conexión con Spotify
Se creó una app en el Spotify Developer Dashboard.

Se configuró el Client ID, Client Secret y el Redirect URI:

http://127.0.0.1:8888/callback
Se usó la librería Spotipy para manejar OAuth y obtener el Access Token automáticamente.
Con el token, la app puede:
Buscar canciones (search)
Obtener información de artista, álbum y previews

⚠️ Nota: Los tokens de acceso expiran cada 1 hora, pero Spotipy los renueva automáticamente durante la ejecución del programa.

Estructura del proyecto
ReproductorMusicaTP/
│
├─ main.py            ← Interfaz Tkinter y lógica principal
├─ spotify_api.py     ← Funciones para conectar y buscar en Spotify
├─ player.py          ← Funciones de reproducción de previews con pygame
├─ assets/            ← Carpeta para imágenes y recursos
├─ requirements.txt   ← Librerías necesarias (spotipy, pygame, Pillow, etc.)
└─ README.md          ← Documentación y bitácora