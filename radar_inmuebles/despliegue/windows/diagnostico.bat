@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0..\..\.."

echo.
echo  ========================================
echo    DIAGNOSTICO DE RED PARA PIP
echo  ========================================
echo.
echo  Sacale una captura a TODO esto y mandamela.
echo.

echo  --- 1. Python ---------------------------------------------
py -3 --version 2>nul || python --version 2>nul || echo  NO HAY PYTHON
where python 2>nul
echo.

echo  --- 2. Proxy de Windows -----------------------------------
netsh winhttp show proxy
echo.

echo  --- 3. Proxy en variables de entorno -----------------------
echo  HTTP_PROXY  = "%HTTP_PROXY%"
echo  HTTPS_PROXY = "%HTTPS_PROXY%"
echo  NO_PROXY    = "%NO_PROXY%"
echo.

echo  --- 4. Configuracion propia de pip -------------------------
if exist "%APPDATA%\pip\pip.ini" (
    echo  HAY un pip.ini en %APPDATA%\pip\
    type "%APPDATA%\pip\pip.ini"
) else (
    echo  No hay pip.ini de usuario.
)
echo.

echo  --- 5. DNS: a que IP resuelve PyPI -------------------------
nslookup files.pythonhosted.org 2>nul | findstr /i "Address Direccion"
echo.

echo  --- 6. Conexion a PyPI (lo que falla) ----------------------
curl.exe -s -o nul -w "  pypi.org            -> HTTP %%{http_code} en %%{time_total}s\n" --max-time 15 https://pypi.org/simple/ 2>nul
curl.exe -s -o nul -w "  files.pythonhosted  -> HTTP %%{http_code} en %%{time_total}s\n" --max-time 15 https://files.pythonhosted.org/ 2>nul
echo.

echo  --- 7. Conexion a otros sitios, para comparar --------------
curl.exe -s -o nul -w "  github.com          -> HTTP %%{http_code}\n" --max-time 15 https://github.com 2>nul
curl.exe -s -o nul -w "  api.telegram.org    -> HTTP %%{http_code}\n" --max-time 15 https://api.telegram.org 2>nul
curl.exe -s -o nul -w "  zonaprop.com.ar     -> HTTP %%{http_code}\n" --max-time 15 https://www.zonaprop.com.ar 2>nul
echo.

echo  --- 8. Antivirus instalado ---------------------------------
powershell -NoProfile -Command "try { Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct | Select-Object -ExpandProperty displayName } catch { 'no pude consultarlo' }" 2>nul
echo.

echo  ========================================
echo    FIN - mandame la captura completa
echo  ========================================
echo.
echo  Si en el punto 6 ves HTTP 000 pero en el 7 ves 200,
echo  algo esta bloqueando PyPI especificamente:
echo  suele ser el antivirus o el firewall de la red.
echo.
pause
