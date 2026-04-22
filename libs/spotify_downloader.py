"""Módulo simplificado para descargar canciones de Spotify usando YouTube"""

import os
import yt_dlp
from pathlib import Path
import subprocess
import sys


def sanitize_filename(name):
    invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\0']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name.strip()

def get_spotify_track_name(sp, url):
    try:
        track_id = url.split('/track/')[-1].split('?')[0]
        track = sp.track(track_id)
        name   = track.get('name', 'Unknown')
        artist = track['artists'][0]['name'] if track.get('artists') else 'Unknown'
        album  = track['album']['name'] if track.get('album') else 'Unknown'
        image  = track['album']['images'][0]['url'] if track['album']['images'] else None
        return {"query": f"{artist} - {name}", "name": name, "artist": artist, "album": album, "image": image}
    except Exception:
        return None

def download_youtube_audio(query, output_path, filename):
    try:
        os.makedirs(output_path, exist_ok=True)

        ffmpeg_location = None
        try:
            import imageio_ffmpeg
            ffmpeg_location = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass

        output_template = os.path.join(output_path, f"{filename}.%(ext)s")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'logtostderr': False,
            'postprocessors': [],
            'logger': type('NullLogger', (), {
                'debug':   lambda self, msg: None,
                'info':    lambda self, msg: None,
                'warning': lambda self, msg: None,
                'error':   lambda self, msg: None,
            })(),
        }

        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_location)

        try:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(f"ytsearch1:{query}", download=True)
            return True

        except Exception:
            ydl_opts['postprocessors'] = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                ext = info.get('ext', 'webm')
                # Limpiar archivo sin extensión si existe
                bare = os.path.join(output_path, filename)
                if os.path.isfile(bare):
                    try:
                        os.remove(bare)
                    except Exception:
                        pass
            return True

    except Exception:
        return False


def download_track(sp, track_url, output_dir='downloads'):
    data = get_spotify_track_name(sp, track_url)
    if not data:
        return None
    clean_name = sanitize_filename(data["query"])
    track_dir  = os.path.join(output_dir, clean_name)
    if download_youtube_audio(data["query"], track_dir, clean_name):
        return track_dir
    return None