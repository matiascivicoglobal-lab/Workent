@echo off
chcp 65001 >nul
cd /d "%~dp0..\..\.."
set "VPY=.venv\Scripts\python.exe"
if not exist "%VPY%" goto :sin_instalar

echo.
echo  Se va a abrir una ventana de Chromium con Facebook.
echo  Inicia sesion normalmente y despues volve aca y apreta Enter.
echo.
echo  Tu usuario y contrasena NO se guardan en ningun archivo
echo  del proyecto: queda una sesion del navegador, como cuando
echo  te quedas logueado en Chrome.
echo.
pause
"%VPY%" -m radar_inmuebles login-facebook
pause
exit /b 0

:sin_instalar
echo.
echo  [X] Primero ejecuta instalar.bat
echo.
pause
exit /b 1
