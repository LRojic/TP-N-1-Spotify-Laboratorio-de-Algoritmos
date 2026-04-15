import pygame
import os
import threading
import time

# Inicializar mixer con manejo de errores
print("🔊 Inicializando pygame.mixer...")
try:
    pygame.mixer.init()
    print("   ✅ pygame.mixer inicializado")
    AUDIO_AVAILABLE = True
except Exception as e:
    print(f"   ⚠️  Error inicializando pygame.mixer: {e}")
    print(f"   💡 Algunos controles de audio pueden no funcionar")
    AUDIO_AVAILABLE = False

# Estado global
pausado = False
reproduciendo = False

def reproducir(ruta):
    """Reproduce un archivo de audio"""
    global pausado, reproduciendo
    print(f"\n🎵 REPRODUCIR: {ruta}")

    if not AUDIO_AVAILABLE:
        print(f"   ❌ Audio no disponible en el sistema")
        return

    if not os.path.exists(ruta):
        print(f"   ❌ Archivo NO existe: {ruta}")
        return

    print(f"   ✅ Archivo existe ({os.path.getsize(ruta)} bytes)")

    def hilo_reproduccion():
        global pausado, reproduciendo
        try:
            print(f"   📂 Cargando en pygame...")
            pygame.mixer.music.load(ruta)
            print(f"   ▶️ Iniciando reproducción...")
            pygame.mixer.music.play()

            pausado = False
            reproduciendo = True
            print(f"   ✅ Reproducción activa")
            
            # El bucle mantiene el hilo vivo mientras suene o esté en pausa
            while pygame.mixer.music.get_busy() or pausado:
                time.sleep(0.5)

            reproduciendo = False
            print(f"   ✅ Reproducción completada")

        except Exception as e:
            print(f"   ❌ Error en pygame: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            reproduciendo = False

    thread = threading.Thread(target=hilo_reproduccion, daemon=True)
    thread.start()
    print(f"   🧵 Thread de reproducción iniciado")


def pausar():
    """Pausa la música"""
    global pausado
    if not AUDIO_AVAILABLE:
        print(f"⏸️ PAUSAR (audio no disponible)")
        return
    
    print(f"⏸️ PAUSAR (get_busy={pygame.mixer.music.get_busy()})")
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        pausado = True
        print("   ✅ Pausado")
    else:
        print("   ❌ No hay música reproduciéndose")


def reanudar():
    """Reanuda la música"""
    global pausado
    if not AUDIO_AVAILABLE:
        print(f"▶️ REANUDAR (audio no disponible)")
        return
    
    print(f"▶️ REANUDAR (pausado={pausado})")
    if pausado:
        pygame.mixer.music.unpause()
        pausado = False
        print("   ✅ Reanudado")
    else:
        print("   ❌ Música no está pausada")


def stop():
    """Detener música"""
    global pausado, reproduciendo
    print(f"⏹️ STOP (reproduciendo={reproduciendo})")
    if not AUDIO_AVAILABLE:
        print("   ❌ Audio no disponible")
        return
    
    pygame.mixer.music.stop()
    pausado = False
    reproduciendo = False
    print("   ✅ Detenido")
# ────────── NUEVAS FUNCIONES PARA LA BARRA ──────────

# Variable para rastrear el tiempo acumulado por saltos manuales
tiempo_inicio_salto = 0

def get_pos():
    """Retorna la posición real de la canción en segundos"""
    global tiempo_inicio_salto
    if not AUDIO_AVAILABLE:
        return 0
    if reproduciendo:
        # get_pos() de pygame da el tiempo transcurrido desde el último play()
        # Le sumamos el tiempo donde empezó el último salto
        return (pygame.mixer.music.get_pos() / 1000) + tiempo_inicio_salto
    return 0

def set_pos(segundos):
    """Salta a una posición específica reiniciando el play desde ese punto"""
    global tiempo_inicio_salto, reproduciendo, pausado
    if not AUDIO_AVAILABLE:
        print(f"⏩ SEEK (audio no disponible)")
        return
    if reproduciendo:
        try:
            # Guardamos el punto de inicio para que get_pos() no se resetee a 0
            tiempo_inicio_salto = segundos
            
            # Reiniciamos la música desde el segundo elegido
            pygame.mixer.music.play(start=segundos)
            
            # Si estaba pausado, lo despausamos automáticamente al saltar
            pausado = False
            
            print(f"⏩ Posición cambiada a: {segundos}s")
        except Exception as e:
            print(f"❌ Error al saltar: {e}")