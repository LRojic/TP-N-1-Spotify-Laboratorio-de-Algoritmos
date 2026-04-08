"""Módulo simplificado para descargar canciones de Spotify usando YouTube"""

import os
import yt_dlp
from pathlib import Path
import subprocess
import sys


def sanitize_filename(name):
    """Limpia caracteres inválidos del nombre de archivo"""
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\0']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name.strip()


def get_spotify_track_name(sp, url):
    """Extrae nombre y artista de una URL de Spotify"""
    try:
        # Parsear URL: https://open.spotify.com/track/ID
        track_id = url.split('/track/')[-1].split('?')[0]
        track = sp.track(track_id)
        
        name = track.get('name', 'Unknown')
        artist = track['artists'][0]['name'] if track.get('artists') else 'Unknown'
        
        return f"{artist} - {name}", name, artist
    except Exception as e:
        print(f"❌ Error al obtener datos de Spotify: {e}")
        return None, None, None


def download_youtube_audio(query, output_path, filename):
    """Descarga audio de YouTube usando yt-dlp (Python puro, sin subprocess)"""
    try:
        os.makedirs(output_path, exist_ok=True)
        
        # Obtener ruta de ffmpeg de imageio_ffmpeg si está disponible
        ffmpeg_location = None
        try:
            import imageio_ffmpeg
            ffmpeg_location = imageio_ffmpeg.get_ffmpeg_exe()
        except:
            pass
        
        # Usar %(ext)s para que yt-dlp añada automáticamente la extensión
        output_template = os.path.join(output_path, f"{filename}.%(ext)s")
        
        # Configurar yt-dlp para descargar el mejor audio disponible
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
            'postprocessors': [],
        }
        
        # Si ffmpeg está disponible, agregar ubicación
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_location)
        
        try:
            # Intentar con ffmpeg para convertir a mp3
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"📥 Buscando y descargando con FFmpeg: {query}")
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                final_file = f"{filename}.mp3"
                print(f"✅ Descargado como MP3: {final_file}")
                return True
                
        except Exception as ffmpeg_error:
            # Si ffmpeg no está disponible, descargar solo audio sin convertir
            print(f"⚠️ FFmpeg no funciona: {ffmpeg_error}")
            print(f"⚠️ Intentando descarga sin conversión...")
            
            # Limpiar postprocessors para descarga sin conversión
            ydl_opts['postprocessors'] = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"📥 Descargando audio original: {query}")
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                
                # yt-dlp añadió automáticamente la extensión gracias a %(ext)s
                ext = info.get('ext', 'webm')
                final_file = f"{filename}.{ext}"
                
                # Limpiar archivos sin extensión o duplicados
                for file in os.listdir(output_path):
                    file_path = os.path.join(output_path, file)
                    # Eliminar archivo sin extensión si existe
                    if file == filename and os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            print(f"🗑️  Limpiado archivo sin extensión")
                        except:
                            pass
                
                print(f"✅ Descargado como {ext.upper()}: {final_file}")
                return True
                
    except Exception as e:
        print(f"❌ Error descargando: {e}")
        return False


def download_track(sp, track_url, output_dir='downloads'):
    """Descarga una canción de Spotify"""
    track_name, name, artist = get_spotify_track_name(sp, track_url)
    
    if not track_name:
        return None
    
    clean_name = sanitize_filename(track_name)
    track_dir = os.path.join(output_dir, clean_name)
    
    print(f"📥 Descargando: {track_name}")
    
    if download_youtube_audio(track_name, track_dir, clean_name):
        return track_dir
    
    return None
