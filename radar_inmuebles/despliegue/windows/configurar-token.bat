@echo off
chcp 65001 >nul
cd /d "%~dp0..\..\.."
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" goto :sin_instalar

echo.
echo  ========================================
echo    Guardar el token de Telegram
echo  ========================================
echo.
echo  Pega abajo el token que te dio @BotFather.
echo  Se ve asi:  123456789:AAHxxxxxxxxxxxxxxxxxxxx
echo.
echo  Para pegar: boton derecho del mouse en esta ventana.
echo.

set "TOKEN="
set /p TOKEN="  Token: "
if not defined TOKEN goto :vacio

"%VPY%" -m radar_inmuebles guardar-token --token "%TOKEN%"
if errorlevel 1 goto :fin

echo  Ahora:
echo    1. Escribile "hola" a tu bot en Telegram
echo    2. Ejecuta  probar.bat
echo.

:fin
pause
exit /b 0

:vacio
echo.
echo  [X] No pegaste nada.
echo.
pause
exit /b 1

:sin_instalar
echo.
echo  [X] Primero ejecuta instalar.bat
echo.
pause
exit /b 1
