#!/bin/bash

echo "=========================================="
echo "  Sistema de Gestion Hotelera (SGH)"
echo "=========================================="
echo ""

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

echo "Activando entorno virtual..."
source venv/bin/activate

echo "Instalando dependencias..."
pip install -q -r requirements.txt

echo ""
echo "Iniciando SGH..."
echo ""
python main.py

echo ""
echo "Cerrando..."
deactivate
