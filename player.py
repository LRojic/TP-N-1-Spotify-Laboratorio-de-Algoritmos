import pygame
import os
import threading
import time

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
pygame.mixer.init()

_pausado = False
_reproduciendo = False
_pos_pausado = 0.0       # posición en segundos cuando se pausó
_tiempo_unpause = 0      # tick de pygame.mixer al reanudar (get_pos referencia desde acá)


def get_pos() -> float:
    if _pausado:
        return _pos_pausado
    if not pygame.mixer.music.get_busy():
        return -1
    raw = pygame.mixer.music.get_pos()   # ms desde último play/unpause
    if raw < 0:
        return -1
    return _pos_pausado + (raw - _tiempo_unpause) / 1000.0


def set_pos(seconds: float):
    global _pos_pausado, _tiempo_unpause
    try:
        _pos_pausado = seconds
        _tiempo_unpause = 0
        pygame.mixer.music.set_pos(seconds)
    except Exception:
        pass


def set_volume(volumen: float):
    """Establece el volumen (0.0 a 1.0)"""
    pygame.mixer.music.set_volume(max(0.0, min(1.0, volumen)))


def reproducir(ruta: str):
    global _pausado, _reproduciendo, _pos_pausado, _tiempo_unpause

    if not os.path.exists(ruta):
        return

    def _hilo():
        global _pausado, _reproduciendo, _pos_pausado, _tiempo_unpause
        try:
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.play()
            _pausado = False
            _reproduciendo = True
            _pos_pausado = 0.0
            _tiempo_unpause = 0

            while pygame.mixer.music.get_busy() or _pausado:
                time.sleep(0.2)

            _reproduciendo = False
            if _on_finish_callback:          # ← llamar al terminar
                _on_finish_callback()

        except Exception:
            _reproduciendo = False
    threading.Thread(target=_hilo, daemon=True).start()


def pausar():
    global _pausado, _pos_pausado
    if pygame.mixer.music.get_busy():
        _pos_pausado = get_pos()    # guardar posición exacta antes de pausar
        pygame.mixer.music.pause()
        _pausado = True


def reanudar():
    global _pausado, _tiempo_unpause
    if _pausado:
        _tiempo_unpause = pygame.mixer.music.get_pos()  # get_pos() va a devolver 0 acá, pero lo capturamos igual
        pygame.mixer.music.unpause()
        _tiempo_unpause = pygame.mixer.music.get_pos()  # capturar DESPUÉS del unpause
        _pausado = False


def stop():
    global _pausado, _reproduciendo, _pos_pausado, _tiempo_unpause
    pygame.mixer.music.stop()
    _pausado = False
    _reproduciendo = False
    _pos_pausado = 0.0
    _tiempo_unpause = 0

_on_finish_callback = None

def set_on_finish(callback):
    global _on_finish_callback
    _on_finish_callback = callback