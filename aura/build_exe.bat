@echo off
chcp 65001 >nul
echo.
echo  ==========================================
echo   Aura: Escudo Etico - Generador de EXE
echo   Hackathon 8M - IEEE WIE
echo  ==========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado.
    pause & exit /b 1
)

echo [1/3] Instalando dependencias...
pip install pynput plyer pystray Pillow pyinstaller --quiet
if errorlevel 1 (
    echo ERROR al instalar dependencias.
    pause & exit /b 1
)

echo.
echo [2/3] Compilando EXE...
echo       Esto puede tardar 1-2 minutos...
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "AuraEscudoEtico" ^
    --hidden-import pynput.keyboard._win32 ^
    --hidden-import pynput.mouse._win32 ^
    --hidden-import plyer.platforms.win.notification ^
    --hidden-import pystray._win32 ^
    --hidden-import PIL._tkinter_finder ^
    --collect-all pynput ^
    --collect-all pystray ^
    --collect-all plyer ^
    --collect-all PIL ^
    aura_escudo_etico.py

echo.
if exist "dist\AuraEscudoEtico.exe" (
    echo [3/3] EXE generado!
    echo.
    echo   Archivo: dist\AuraEscudoEtico.exe
    echo.
    echo   IMPORTANTE: Ejecutar como Administrador
    echo   para habilitar bloqueo de sitios web.
    echo.
    explorer dist
) else (
    echo ERROR: No se genero el EXE.
)
pause
