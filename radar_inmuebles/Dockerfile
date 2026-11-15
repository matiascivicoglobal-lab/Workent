FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=America/Argentina/Buenos_Aires \
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw

WORKDIR /app

COPY radar_inmuebles/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt playwright==1.49.0 \
 && playwright install --with-deps chromium

COPY radar_inmuebles /app/radar_inmuebles

# La base y el reporte viven en un volumen para sobrevivir al redeploy.
VOLUME ["/app/radar_inmuebles/datos"]

CMD ["python", "-m", "radar_inmuebles", "watch"]
