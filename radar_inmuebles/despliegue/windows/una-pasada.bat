@echo off
chcp 65001 >nul
title Radar Inmuebles - una pasada
cd /d "%~dp0..\..\.."
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" goto :sin_instalar

rem Una sola busqueda y cierra. Util para probar o para el Programador de tareas.
"%VPY%" -m radar_inmuebles scan
echo.
echo  Reporte completo: radar_inmuebles\datos\reporte.html
echo.
pause
exit /b 0

:sin_instalar
echo.
echo  [X] Primero ejecuta instalar.bat
echo.
pause
exit /b 1
