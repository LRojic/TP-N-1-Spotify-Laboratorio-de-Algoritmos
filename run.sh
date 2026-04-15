#!/bin/bash
# Script para iniciar el reproductor de música

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     🎵 Reproductor de Música - Python + PyQt5                 ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar entorno virtual
if [ ! -d ".venv/bin" ]; then
    echo "⚠️ Entorno virtual no encontrado. Creando..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Error creando entorno virtual"
        exit 1
    fi
    source .venv/bin/activate
    pip install -q -r requirements.txt
    echo "✅ Dependencias instaladas"
else
    source .venv/bin/activate
fi

echo "✅ Iniciando reproductor..."
echo ""
python main.py
