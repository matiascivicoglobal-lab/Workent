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

**Conectá el canal de avisos.** Elegí uno:

### Telegram — 2 minutos, gratis, nunca se cae

1. En Telegram, hablale a **@BotFather** → `/newbot` → elegí un nombre.
   Te da un token tipo `123456:ABC-DEF...`
2. Escribile algo a tu bot recién creado (un "hola" alcanza).
3. Abrí `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` en el navegador y
   buscá `"chat":{"id":123456789`. Ese número es tu chat id.
4. En `radar_inmuebles/.env`:
   ```
   TELEGRAM_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=123456789
   ```
5. En `config.yaml`: `alertas.destino: telegram`

### WhatsApp vía CallMeBot — gratis, pero depende de un tercero

1. Mirá el número vigente en
   [callmebot.com](https://www.callmebot.com/blog/free-api-whatsapp-messages/)
   (cambia cada tanto).
2. Agendalo y mandale: `I allow callmebot to send me messages`
3. Te responde con tu *apikey*. Pegala en `radar_inmuebles/.env`:
   `CALLMEBOT_APIKEY=123456`

> **Si te responde "This Bot is full":** el servicio no está tomando usuarios
> nuevos. No es un problema de tu configuración y no hay nada que puedas
> hacer del lado del bot. Ver la sección siguiente.

### WhatsApp oficial (Meta Cloud API) — gratis y para siempre, pero lleva rato

Ver [más abajo](#whatsapp-oficial-meta-cloud-api).

---

## Si CallMeBot está lleno

Es un servicio gratuito mantenido por una sola persona y se satura seguido.
Tres caminos, de más rápido a más robusto:

| Camino | Tiempo | Cómo se ve el aviso | Aguanta |
|---|---|---|---|
| **Telegram** | 2 min | igual que el ejemplo, con negritas | para siempre |
| **Twilio sandbox** | 15 min | igual | se corta cada 24 h |
| **Meta Cloud API** | ~40 min | en una sola línea | para siempre |

**Mi recomendación: Telegram ahora, Meta Cloud API cuando tengas un rato.**
El bot ya quedó configurado con `alertas.respaldo: telegram`, así que si
configurás los dos, cuando CallMeBot vuelva a abrir el aviso sale por WhatsApp
y si se cae otra vez sale por Telegram solo, sin que toques nada.

Probá cualquier canal sin editar la config:

```bash
python -m radar_inmuebles probar-aviso --canal telegram
python -m radar_inmuebles probar-aviso --canal whatsapp:cloud
```

### Twilio sandbox (el atajo con asterisco)

Rápido de configurar, pero WhatsApp solo te deja recibir mensajes libres
durante **24 horas** desde tu último mensaje al bot. O sea: tendrías que
escribirle al sandbox una vez por día o los avisos dejan de llegar. Sirve para
probar, no para dejarlo corriendo.

1. Cuenta gratis en twilio.com → Messaging → Try it out → WhatsApp sandbox.
2. Mandá el código `join <dos-palabras>` al número que te muestran.
3. En el `.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` y
   `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886`
4. En `config.yaml`: `proveedor_whatsapp: twilio`

### WhatsApp oficial (Meta Cloud API)

Es la vía que no depende de nadie. Gratis para este volumen y sin riesgo para
tu cuenta personal, porque usás un número de prueba que te da Meta.

1. **developers.facebook.com** → Mis apps → Crear app → tipo **Empresa**.
2. Agregá el producto **WhatsApp** → Configurar. Te crea una cuenta de Meta
   Business y te da un **número de prueba**.
3. En "Configuración de la API": agregá tu celular como destinatario y
   verificalo con el código que te llega. Copiá el **identificador del número
   de teléfono** → ese es `WA_PHONE_NUMBER_ID`.
4. **Token permanente** (el que te muestra ahí dura 24 h):
   business.facebook.com → Configuración del negocio → Usuarios → **Usuarios
   del sistema** → Agregar → asignale la app y la cuenta de WhatsApp →
   Generar token → permisos `whatsapp_business_messaging` y
   `whatsapp_business_management` → caducidad **Nunca**. Ese es `WA_TOKEN`.
5. **Plantilla** (obligatoria para mensajes automáticos): WhatsApp Manager →
   Plantillas de mensajes → Crear → categoría **Utilidad**, idioma Español,
   cuerpo con una variable:
   ```
   {{1}}
   ```
   Nombrala `aviso_propiedad`. Se aprueba en minutos.
6. En el `.env`:
   ```
   WA_PHONE_NUMBER_ID=123456789
   WA_TOKEN=EAAG...
   WA_TEMPLATE=aviso_propiedad
   WA_TEMPLATE_LANG=es
   ```
7. En `config.yaml`: `proveedor_whatsapp: cloud`

> **Por qué el aviso se ve peor acá:** WhatsApp no permite saltos de línea
> dentro de las variables de plantilla. El bot aplana el mensaje a una sola
> línea con separadores `·`. Tiene toda la información, pero se lee menos
> cómodo que por Telegram.

Probá que todo esté en orden:

```bash
python -m radar_inmuebles demo              # cómo se ve un aviso (sin red)
python -m radar_inmuebles probar-aviso      # te manda un mensaje de prueba
python -m radar_inmuebles verificar         # qué portales están respondiendo
python -m radar_inmuebles scan              # una pasada real
python -m radar_inmuebles watch             # queda monitoreando
```

---

## Antes de dejarlo corriendo

**Tu presupuesto ya está cargado: USD 80.000** (`config.yaml → busqueda`).

Con ese techo, esto es lo que podés esperar de cada barrio:

| Barrio | Mediana estimada | Un 3 amb de 65 m² al valor de zona | A USD 80.000 estarías comprando |
|---|---|---|---|
| Liniers | ~1.550 USD/m² | ~100.000 | normal, con descuento del 15-25% |
| Villa Luro | ~1.750 USD/m² | ~114.000 | unidades chicas o para reciclar |
| Caballito | ~2.250 USD/m² | ~146.000 | solo 45-55 m² antiguos, o algo con un problema |

Traducido: **la mayoría de las alertas te van a llegar de Liniers y Villa Luro.**
Lo que aparezca de Caballito a USD 80.000 va a venir marcado `⚠️ verificar` muy
seguido, y con razón: a ese precio en ese barrio casi siempre hay un motivo.
No es un error del bot, es el mercado.

Si querés más volumen de avisos, las tres palancas, en orden de impacto:

```yaml
busqueda:
  precio_usd_max: 95000        # la que más mueve la aguja
  ambientes_max: 4             # incluir 3 y 4 ambientes
oportunidad:
  descuento_minimo: 0.12       # hoy está en 0.15
```

**Las primeras 2-3 corridas no sirven para avisar.** El radar necesita juntar
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

**Te avisa** cuando `descuento ≥ 15%` **y** `puntaje ≥ 50`. Lo cambiás en
`config.yaml → oportunidad`.

### Lo que también mira

- **Señales en el texto**: "a reciclar", "dueño directo", "escucho ofertas",
  "sucesión", "urge". Suman puntaje.
- **Riesgos excluyentes**: nuda propiedad, usufructo, en pozo, ocupado, sin
  escritura. Esos **no te los manda**, por más barato que esté.
- **Bajas de precio**: guarda el historial de cada aviso. Si uno que ya viste
  baja 4% o más, te vuelve a avisar. Un aviso que lleva 90 días y bajó dos veces
  es un vendedor que quiere salir.
- **Precios sospechosos**: si está más de 45% abajo del mercado, te lo manda
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
| Facebook Marketplace | tu sesión — pide `login-facebook` primero | **sí** |

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

**Está activado** (`fuentes.facebook.activa: true`), pero necesita un paso
manual tuyo antes de la primera corrida:

```bash
python -m radar_inmuebles login-facebook
```

Se abre Chromium, iniciás sesión a mano una vez, cerrás. Queda un perfil
guardado en `radar_inmuebles/datos/perfil_chromium`. **Nunca se guarda tu
usuario ni tu contraseña en ningún archivo del proyecto.**

Lo que tenés que saber, sin vueltas:

- Marketplace no tiene API. La única forma de leerlo es abrir el sitio con tu
  sesión iniciada, y **las Condiciones de Facebook prohíben el acceso
  automatizado**. El riesgo real es que Facebook te marque o bloquee la cuenta.
- Por eso está configurado con `cada_minutos: 90`: aunque el radar corra cada
  45 minutos, Facebook se consulta como mucho cada hora y media. **No bajes ese
  número de 60.**
- Los datos que trae son pobres: Marketplace no publica m² en un campo
  estructurado, así que muchos avisos van a quedar sin tasar. Sirve para
  detectar dueños directos que no publican en portales, no para el análisis
  de precio por m².
- Si preferís cortar el riesgo en cualquier momento: poné `activa: false`.

Alternativa sin riesgo, que podés usar en paralelo: creá la búsqueda en
Marketplace desde tu celular y activá las notificaciones de publicaciones
nuevas. No te da el análisis, pero no arriesga nada.

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
| `probar-aviso` | Manda un mensaje de prueba (`--canal telegram` para probar otro) |
| `login-facebook` | Abre el navegador para iniciar sesión |

Flags útiles: `--sin-enviar` (corre todo pero no manda el aviso),
`--canal telegram` (pisa el canal configurado, sin editar nada),
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
  descuento_minimo: 0.15      # bajalo a 0.12 si te llegan pocos avisos
  puntaje_minimo: 50          # subilo a 65 si te llegan demasiados
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

118 tests, todos offline: parseo de precios argentinos, medianas robustas,
scoring, detección de bajas de precio, dedupe entre portales, armado del mensaje
y el pipeline completo de punta a punta con una fuente falsa.

Los tests usan su propio `tests/config_test.yaml`, así que podés ajustar tu
`config.yaml` sin romperlos. Hay además un test que valida que tu config siga
siendo coherente (rango de precios, teléfono, barrios con valor semilla,
Facebook espaciado).
