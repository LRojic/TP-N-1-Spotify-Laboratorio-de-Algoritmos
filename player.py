import pygame
import requests
from io import BytesIO

pygame.mixer.init()

def play_preview(preview_url):
    if preview_url:
        response = requests.get(preview_url)
        with BytesIO(response.content) as f:
            pygame.mixer.music.load(f)
            pygame.mixer.music.play()
    else:
        print("No hay preview disponible")

def stop():
    pygame.mixer.music.stop()