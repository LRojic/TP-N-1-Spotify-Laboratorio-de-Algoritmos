# player.py

import pygame
import os
import threading
import time

# Inicializar mixer
print("Inicializando pygame.mixer...")
pygame.mixer.init()
print("   pygame.mixer inicializado")

# Estado global
pausado = False
reproduciendo = False


def get_pos():
    """Devuelve la posición actual en segundos (-1 si no hay nada)"""
    pos_ms = pygame.mixer.music.get_pos()
    if pos_ms == -1:
        return -1
    return pos_ms / 1000


def set_pos(seconds: float):
    """Salta a una posición en segundos"""
    try:
        pygame.mixer.music.set_pos(seconds)
    except Exception as e:
        print(f"⚠️ set_pos error: {e}")


def reproducir(ruta):
    """Reproduce un archivo de audio"""
    global pausado, reproduciendo

    if not os.path.exists(ruta):
        print(f"❌ No existe el archivo: {ruta}")
        return

    def hilo_reproduccion():
        global pausado, reproduciendo
        try:
            print(f"▶️ Cargando: {os.path.basename(ruta)}")
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.play()

            pausado = False
            reproduciendo = True

            print(f"▶️ Reproduciendo: {os.path.basename(ruta)}")

            while pygame.mixer.music.get_busy() or pausado:
                time.sleep(0.5)

            reproduciendo = False
            print(f"✅ Reproducción completada: {os.path.basename(ruta)}")

        except Exception as e:
            print(f"❌ Error reproduciendo: {e}")
            reproduciendo = False

    threading.Thread(target=hilo_reproduccion, daemon=True).start()


def pausar():
    """Pausa la música"""
    global pausado
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        pausado = True
        print("⏸️ Música pausada")


def reanudar():
    """Reanuda la música"""
    global pausado
    if pausado:
        pygame.mixer.music.unpause()
        pausado = False
        print("▶️ Música reanudada")


def stop():
    """Detener música"""
    global pausado, reproduciendo
    pygame.mixer.music.stop()
    pausado = False
    reproduciendo = False
    print("⏹️ Música detenida")
