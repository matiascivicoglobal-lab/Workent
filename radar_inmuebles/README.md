# Radar Inmuebles — CABA

Bot que mira todo el día los portales de venta de propiedades, calcula cuánto
vale el m² en cada barrio y te manda un WhatsApp cuando aparece algo
claramente por debajo de ese valor.

Está configurado para lo que buscás: **3 ambientes en Caballito, Villa Luro o
Liniers**, para reciclar y revender.

Así llega el aviso:

```
🔥 OPORTUNIDAD  ·  95/100
Caballito · 3 amb · 68 m²
USD 96.000  (USD 1.412/m²)
──────────────────
📊 La zona está en USD 2.250/m² y esta en USD 1.412/m²
👉 37% más barata que la mediana del barrio
   (sobre 64 avisos comparables · confianza alta)
📉 Bajó 14% (USD 112.000 → USD 96.000) en 23 días
📅 Publicado hace 3 meses
──────────────────
Si la reciclás:
🔨 Obra estimada: USD 27.200
💰 Inversión total: USD 128.960
🏷️ Valor reciclada: USD 176.800
📈 Margen neto de comisión: USD 40.768 (+32%)
──────────────────
🔎 a reciclar · estado original · dueño directo · escucha ofertas
🧾 Expensas: $85.000
🔗 https://...
```

---

## Arranque rápido

```bash
cd Workent
pip install -r radar_inmuebles/requirements.txt

# Opcional pero recomendado (habilita Zonaprop):
pip install playwright && playwright install chromium

cp radar_inmuebles/.env.example radar_inmuebles/.env
```

**Conectá el WhatsApp** (2 minutos, gratis):

1. Agendá el número **+34 644 51 95 23** como "CallMeBot".
2. Mandale por WhatsApp: `I allow callmebot to send me messages`
3. Te responde con tu *apikey*. Pegala en `radar_inmuebles/.env`:
   `CALLMEBOT_APIKEY=123456`

Probá que todo esté en orden:

```bash
python -m radar_inmuebles demo              # cómo se ve un aviso (sin red)
python -m radar_inmuebles probar-whatsapp   # te manda un mensaje de prueba
python -m radar_inmuebles verificar         # qué portales están respondiendo
python -m radar_inmuebles scan              # una pasada real
python -m radar_inmuebles watch             # queda monitoreando
```

---

## Antes de dejarlo corriendo: dos cosas que tenés que tocar

**1. Tu presupuesto.** En `config.yaml`:

```yaml
busqueda:
  precio_usd_min: 40000      # debajo de esto casi siempre es error o cochera
  precio_usd_max: 160000     # ← poné tu techo real
```

**2. Las primeras 2-3 corridas no sirven para avisar.** El radar necesita juntar
muestra para saber cuánto vale el m² en cada barrio. Hasta entonces usa los
valores semilla del `config.yaml`, que son estimativos. Corré:

```bash
python -m radar_inmuebles scan --sin-enviar   # 2 o 3 veces
python -m radar_inmuebles zonas               # mirá si los valores cierran
```

Cuando `zonas` diga `propia` y `confianza alta`, el radar está calibrado con el
mercado real y los avisos valen.

---

## Cómo decide que algo es una oportunidad

No alcanza con que esté barato: una propiedad a reciclar **tiene** que estar por
debajo del mercado, porque ese descuento es el costo de la obra. Lo que importa
es **el descuento que sobra después de pagar todo**.

```
USD/m² del aviso   = precio / m² (cubiertos si están, si no totales)
USD/m² de la zona  = mediana de los avisos comparables del barrio
                     (recortando outliers por IQR, para que las gangas
                      y los delirios no muevan la referencia)
descuento          = (zona - aviso) / zona

obra               = m² × 400 USD        (reciclado integral, configurable)
inversión          = precio × 1,06 + obra  (escritura, sellos, comisión)
valor reciclada    = m² × p75 de la zona   (lo que vale en buen estado)
margen             = valor × 0,96 - inversión   (neto de comisión de venta)
```

El **puntaje 0-100** combina: descuento vs la zona (40), margen del reciclado (30),
señales del texto (12), antigüedad del aviso (8) y baja de precio (10). Resta por
señales de riesgo y por tener poca muestra en la zona.

**Te avisa** cuando `descuento ≥ 18%` **y** `puntaje ≥ 55`. Lo cambiás en
`config.yaml → oportunidad`.

### Lo que también mira

- **Señales en el texto**: "a reciclar", "dueño directo", "escucho ofertas",
  "sucesión", "urge". Suman puntaje.
- **Riesgos excluyentes**: nuda propiedad, usufructo, en pozo, ocupado, sin
  escritura. Esos **no te los manda**, por más barato que esté.
- **Bajas de precio**: guarda el historial de cada aviso. Si uno que ya viste
  baja 4% o más, te vuelve a avisar. Un aviso que lleva 90 días y bajó dos veces
  es un vendedor que quiere salir.
- **Precios sospechosos**: si está más de 60% abajo del mercado, te lo manda
  igual pero marcado `⚠️ verificar` — casi siempre es un error de carga, una
  cochera clasificada como departamento o una traba legal.
- **El mismo depto en 3 portales**: lo agrupa por barrio + m² + precio y te
  avisa una sola vez.

---

## Fuentes

| Fuente | Cómo entra | Necesita Playwright |
|---|---|---|
| MercadoLibre | API oficial | no |
| Argenprop | HTML | no |
| Properati | JSON embebido | no |
| RE/MAX | API del sitio | no |
| Zonaprop | HTML (tiene Cloudflare) | **sí** |
| Facebook Marketplace | sesión propia — apagado por defecto | **sí** |

**Importante:** los parsers están escritos de forma tolerante (leen el texto de
la tarjeta con expresiones regulares en vez de depender de una clase CSS), pero
**no pude probarlos contra los sitios reales**: el entorno donde se escribió
este bot no tiene salida a esos dominios. La primera vez que lo corras, usá:

```bash
python -m radar_inmuebles verificar
```

Te dice fuente por fuente cuántos avisos trajo y si tienen precio y m². Si
alguna devuelve 0, lo más probable es que haya cambiado la URL de búsqueda o la
estructura de la tarjeta. Podés corregir la URL sin tocar código:

```yaml
fuentes:
  argenprop:
    activa: true
    url_template: "{base}/{tipo}-venta-barrio-{barrio}{ambientes}{pagina}"
```

### Sobre Facebook Marketplace

Está apagado por defecto y conviene dejarlo así. Marketplace no tiene API: la
única forma es abrir el sitio con tu sesión iniciada, y las Condiciones de
Facebook prohíben el acceso automatizado — podés comerte un bloqueo de tu
cuenta. Si aun así lo querés:

```bash
python -m radar_inmuebles login-facebook    # iniciás sesión a mano, una vez
# después poné fuentes.facebook.activa: true y intervalo_minutos ≥ 60
```

Nunca se guarda tu usuario ni tu contraseña: queda un perfil de Chromium en
`radar_inmuebles/datos/perfil_chromium`.

Alternativa sin riesgo: creá la búsqueda en Marketplace desde el celular y
activá las notificaciones de publicaciones nuevas.

---

## Dejarlo corriendo 24/7

**Opción A — tu computadora** (la mejor: IP residencial, los portales no te
bloquean):

```bash
nohup python -m radar_inmuebles watch > radar.log 2>&1 &
```

En Linux con systemd, hay un ejemplo en `despliegue/radar.service`.

**Opción B — Docker** (en tu compu o en un VPS):

```bash
cd radar_inmuebles && docker compose up -d
docker compose logs -f
```

**Opción C — GitHub Actions** (gratis, sin servidor): está en
`.github/workflows/radar.yml`, corre cada hora. Ojo: las IPs de GitHub están
bloqueadas por Cloudflare, así que Zonaprop no va a funcionar desde ahí.
MercadoLibre, Argenprop, Properati y RE/MAX sí. Cargá `CALLMEBOT_APIKEY` en
*Settings → Secrets and variables → Actions*.

> Un VPS barato o un servidor cloud comparten rango de IP con miles de bots.
> Si ves muchos 403, la solución es correrlo en tu casa o configurar
> `RADAR_PROXY` con un proxy residencial.

---

## Comandos

| Comando | Qué hace |
|---|---|
| `scan` | Una pasada completa: busca, evalúa, avisa y genera el reporte |
| `watch` | Lo mismo, en loop, cada `intervalo_minutos` |
| `demo` | Muestra cómo se ve una alerta, sin tocar internet |
| `verificar` | Prueba cada fuente y el canal de WhatsApp |
| `zonas` | Valor del m² por barrio, con tamaño de muestra y confianza |
| `reporte` | Regenera el HTML desde la base, sin volver a scrapear |
| `probar-whatsapp` | Manda un mensaje de prueba |
| `login-facebook` | Abre el navegador para iniciar sesión |

Flags útiles: `--sin-enviar` (corre todo pero no manda WhatsApp),
`--cada 30` (minutos, para `watch`), `-v` (log detallado).

El reporte HTML queda en `radar_inmuebles/datos/reporte.html`: tiene el ranking
completo, no solo lo que pasó el filtro de WhatsApp.

---

## Qué NO hace (para que no te sorprenda)

- **No tasa.** Compara precios de **oferta** publicados, no de cierre. En CABA
  la venta real suele cerrar 5-10% abajo del publicado. Tomá los valores como
  una señal para ir a ver, no como una tasación.
- **No sabe el estado real.** Un depto puede estar 35% abajo porque está
  destruido, porque es un contrafrente al pulmón en planta baja, o porque tiene
  un problema de escritura que no dice el aviso. El bot te lleva a la puerta;
  entrar es tu trabajo.
- **No negocia ni reserva.** Solo avisa.
- **Los m² publicados mienten seguido.** Muchos avisos ponen los totales como
  cubiertos. Verificá en la ficha.

---

## Calibrar el scoring

```yaml
oportunidad:
  descuento_minimo: 0.18      # bajalo a 0.12 si te llegan pocos avisos
  puntaje_minimo: 55          # subilo a 70 si te llegan demasiados
  costo_reforma_usd_m2: 400   # pedí presupuesto real y ajustá esto
```

`costo_reforma_usd_m2` es el que más mueve el margen. 400 USD/m² es un reciclado
integral razonable para CABA (cocina, baño, instalación eléctrica, pisos,
aberturas). Si solo vas a pintar y cambiar pisos, poné 150.

---

## Tests

```bash
cd Workent
python -m unittest discover -s radar_inmuebles/tests -t . -p "test_*.py"
```

91 tests, todos offline: parseo de precios argentinos, medianas robustas,
scoring, detección de bajas de precio, dedupe entre portales, armado del mensaje
y el pipeline completo de punta a punta con una fuente falsa.
