import pygame
import os
import threading
import time

# Inicializar mixer
pygame.mixer.init()

# Estado global
pausado = False
reproduciendo = False

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