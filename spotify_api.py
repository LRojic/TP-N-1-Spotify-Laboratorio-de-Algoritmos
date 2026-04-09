import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

load_dotenv()

def get_spotify_client():
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id="0ad8ce594e68403e93e5506f117dd543",
        client_secret="a6bdea0a577146248d6438a80cc0b615",
        redirect_uri="http://127.0.0.1:8888/callback",
        scope="user-library-read playlist-read-private"
    ))
    return sp

def search_tracks(sp, query, limit=10):
    results = sp.search(q=query, type="track", limit=limit)["tracks"]["items"]
    return results