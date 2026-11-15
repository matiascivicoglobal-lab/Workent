@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0..\..\.."

echo.
echo  ========================================
echo    RADAR INMUEBLES - Instalacion
echo  ========================================
echo.

rem --- Buscar Python. El "py" del instalador oficial tiene prioridad -------
set "PYCMD="
py -3 --version >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"
if not defined PYCMD (
    python --version >nul 2>nul
    if not errorlevel 1 set "PYCMD=python"
)
if not defined PYCMD goto :sin_python

for /f "delims=" %%V in ('%PYCMD% --version 2^>^&1') do set "PYVER=%%V"
echo  Python encontrado: %PYVER%
echo.

rem --- 1. Entorno virtual --------------------------------------------------
echo  [1/4] Preparando el entorno...
if not exist ".venv\Scripts\python.exe" (
    %PYCMD% -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo        Ya estaba creado.
)
set "VPY=.venv\Scripts\python.exe"

rem --- 2. Dependencias -----------------------------------------------------
echo  [2/4] Instalando dependencias (tarda un minuto)...
"%VPY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
"%VPY%" -m pip install -r radar_inmuebles\requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 goto :error_pip

rem --- 3. Navegador para Zonaprop y Facebook -------------------------------
echo  [3/4] Instalando el navegador para Zonaprop y Facebook...
echo        (son unos 130 MB, la primera vez tarda)
"%VPY%" -m pip install playwright==1.49.0 --quiet --disable-pip-version-check
if errorlevel 1 goto :error_pip
"%VPY%" -m playwright install chromium
if errorlevel 1 (
    echo.
    echo  [!] No pude instalar el navegador. El radar va a funcionar igual,
    echo      pero sin Zonaprop ni Facebook. Podes reintentar mas tarde con:
    echo         .venv\Scripts\python.exe -m playwright install chromium
    echo.
)

rem --- 4. Archivo de claves ------------------------------------------------
echo  [4/4] Preparando el archivo de claves...
if exist "radar_inmuebles\.env" (
    echo        Ya existe radar_inmuebles\.env, no lo toco.
) else (
    copy "radar_inmuebles\.env.example" "radar_inmuebles\.env" >nul
    echo.
    echo  ----------------------------------------------------------
    echo   Se va a abrir el Bloc de notas con el archivo de claves.
    echo.
    echo   Pega tu token de Telegram despues del signo = en la linea
    echo   que dice TELEGRAM_TOKEN=
    echo.
    echo   Te tiene que quedar algo asi:
    echo      TELEGRAM_TOKEN=123456789:AAHxxxxxxxxxxxxxxxxxxxx
    echo.
    echo   Guarda con Ctrl+S y cerra el Bloc de notas.
    echo  ----------------------------------------------------------
    echo.
    pause
    notepad "radar_inmuebles\.env"
)

echo.
echo  ========================================
echo    LISTO
echo  ========================================
echo.
echo   Ahora, en este orden:
echo.
echo     1. Abri Telegram y escribile "hola" a tu bot
echo     2. Ejecuta  probar.bat  (doble clic)
echo.
pause
exit /b 0

:sin_python
echo  [X] No encuentro Python instalado.
echo.
echo      Opcion facil: abri la Microsoft Store, busca "Python 3.12"
echo      e instalalo. Despues volve a ejecutar este archivo.
echo.
echo      Opcion manual: https://www.python.org/downloads/
echo      IMPORTANTE: al instalar, tilda "Add python.exe to PATH".
echo.
pause
exit /b 1

:error_pip
echo.
echo  ============================================================
echo   [X] pip no pudo descargar los paquetes.
echo  ============================================================
echo.
echo   Si arriba dice "WinError 10061", "Failed to establish a new
echo   connection" o "Max retries exceeded", el problema NO es el
echo   radar: algo esta bloqueando el acceso a pypi.org.
echo.
echo   Probalos en este orden:
echo.
echo    1. Compartí internet desde el celular (anclaje a red / zona
echo       wifi portatil), conecta la compu ahi y volve a ejecutar
echo       este archivo. Si asi funciona, lo bloquea tu red.
echo.
echo    2. Pausa el antivirus unos minutos y reintenta. El escudo
echo       web de varios antivirus corta las descargas de pip.
echo.
echo    3. Si estas en una red de trabajo, pedi que habiliten
echo       pypi.org y files.pythonhosted.org
echo.
echo   Para saber cual de los tres es, ejecuta  diagnostico.bat
echo   y mandame la captura.
echo.
pause
exit /b 1

:error
echo.
echo  [X] Algo fallo. Copiame el mensaje de error de arriba.
echo.
pause
exit /b 1
