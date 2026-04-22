# playlists.py

import os
import threading
from pathlib import Path
 
CARPETA_DESCARGAS = "downloads"
 
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
        {"nombre": "Sugar",           "artista": "Maroon 5",        "url": "https://open.spotify.com/track/2bL2gyO6kBdLkNSkxXNh6x"},
        {"nombre": "Poker Face",      "artista": "Lady Gaga",       "url": "https://open.spotify.com/track/1QV6tiMFM6fSOKOGLMHYYg"},
        {"nombre": "Hips Don't Lie",  "artista": "Shakira",         "url": "https://open.spotify.com/track/3d0WouFnFmr0K3kjeza3fF"},
        {"nombre": "Hot N Cold",      "artista": "Katy Perry",      "url": "https://open.spotify.com/track/1TEjSXPdAakDotj2Wji3PU"},
        {"nombre": "Single Ladies",   "artista": "Beyoncé",         "url": "https://open.spotify.com/track/5R9a4t5t5O0IsznsrKPVro"},
        {"nombre": "I Gotta Feeling", "artista": "Black Eyed Peas", "url": "https://open.spotify.com/track/4kLLWz7srcuLKA7Et40PQR"},
        {"nombre": "Right Round",     "artista": "Flo Rida",        "url": "https://open.spotify.com/track/3GpbwCm3YxiWDvy29Uo3vP"},
        {"nombre": "Timber",          "artista": "Pitbull ft Kesha","url": "https://open.spotify.com/track/3cHyrEgdyYRjgJKSOiOtcS"},
    ],
}

def _ya_descargada(nombre: str, artista: str) -> bool:
    nombre_carpeta = f"{artista} - {nombre}"
    carpeta = os.path.join(CARPETA_DESCARGAS, nombre_carpeta)
    if not os.path.exists(carpeta):
        return False
    for f in os.listdir(carpeta):
        if f.lower().endswith(('.mp3', '.wav', '.webm')):
            return True
    return False
