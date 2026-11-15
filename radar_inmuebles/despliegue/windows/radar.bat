@echo off
chcp 65001 >nul
title Radar Inmuebles - buscando
cd /d "%~dp0..\..\.."
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" goto :sin_instalar

echo.
echo  El radar esta buscando. Dejalo abierto.
echo  Para cortarlo: Ctrl+C o cerra esta ventana.
echo.

"%VPY%" -m radar_inmuebles watch

echo.
echo  El radar se detuvo.
pause
exit /b 0

:sin_instalar
echo.
echo  [X] Primero ejecuta instalar.bat
echo.
pause
exit /b 1
