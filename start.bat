@echo off
echo ==========================================
echo  Sistema de Gestion Hotelera (SGH)
echo ==========================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo Creando entorno virtual...
    python -m venv venv
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -q -r requirements.txt

echo.
echo Iniciando SGH...
echo.
python main.py

echo.
echo Cerrando...
deactivate
pause
