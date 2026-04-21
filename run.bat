@echo off
REM Script para iniciar el reproductor de música

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║     🎵 Reproductor de Música - Python + PyQt5                 ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Verificar entorno virtual
if not exist ".venv\Scripts\activate.bat" (
    echo ⚠️ Entorno virtual no encontrado. Creando...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Error creando entorno virtual
        pause
        exit /b 1
    )
    call .venv\Scripts\activate.bat
    pip install -q -r requirements.txt
    echo ✅ Dependencias instaladas
) else (
    call .venv\Scripts\activate.bat
)

echo ✅ Iniciando reproductor...
echo.
python main.py
pause
