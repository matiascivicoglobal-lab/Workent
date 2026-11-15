@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo.
echo  Esto hace que el radar arranque solo cada vez que prendas la compu.
echo.
echo  Para deshacerlo despues:
echo     schtasks /delete /tn "Radar Inmuebles" /f
echo.
pause

schtasks /create /tn "Radar Inmuebles" /tr "\"%~dp0radar.bat\"" /sc onlogon /rl limited /f
if errorlevel 1 (
    echo.
    echo  [X] No se pudo crear la tarea. Proba abrir este archivo con
    echo      boton derecho - Ejecutar como administrador.
    echo.
) else (
    echo.
    echo  Listo. El radar va a arrancar solo al prender la compu.
    echo.
)
pause
