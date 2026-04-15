## 🚀 INICIO RÁPIDO

### Requisitos
- Python 3.8+
- Spotify Developer Account (gratis)

### 5 Minutos para empezar:

**1️⃣ Instalar dependencias:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**2️⃣ Configurar Spotify:**
```
1. Ir a: https://developer.spotify.com/dashboard
2. Crear App → Copiar Client ID y Secret
3. Crear .env con:
```
```env
SPOTIFY_CLIENT_ID=tu_id
SPOTIFY_CLIENT_SECRET=tu_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

**3️⃣ Ejecutar:**
```bash
# Windows
run.bat

# Linux/Mac
bash run.sh

# O directamente
python main.py
```

**¡Listo! 🎵**

---

## 🎯 Primera prueba:
1. Escribe "Arctic Monkeys" en el buscador
2. Hace click en "Buscar"
3. Selecciona una canción
4. ▶ Play

¡A disfrutar! 🎧
