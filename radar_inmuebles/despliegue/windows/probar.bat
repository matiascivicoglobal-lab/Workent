@echo off
chcp 65001 >nul
cd /d "%~dp0..\..\.."
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" goto :sin_instalar

echo.
echo  ========================================
echo    1. Buscando tu chat de Telegram
echo  ========================================
"%VPY%" -m radar_inmuebles telegram-chatid --guardar
if errorlevel 1 (
    echo.
    echo  [!] Si dice que no encontro mensajes: abri Telegram,
    echo      escribile "hola" a tu bot y volve a ejecutar este archivo.
    echo.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo    2. Mandando un mensaje de prueba
echo  ========================================
"%VPY%" -m radar_inmuebles probar-aviso
if errorlevel 1 goto :fin

echo.
echo  ========================================
echo    3. Probando los portales
echo  ========================================
echo    (tarda un par de minutos)
"%VPY%" -m radar_inmuebles verificar

echo.
echo  Si te llego el mensaje a Telegram, ya esta.
echo  Ejecuta  radar.bat  para dejarlo buscando.
echo.

:fin
pause
exit /b 0

:sin_instalar
echo.
echo  [X] Primero ejecuta instalar.bat
echo.
pause
exit /b 1
