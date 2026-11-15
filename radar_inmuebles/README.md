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

**Es el canal configurado por defecto** (`alertas.destino: telegram`).

1. En Telegram, hablale a **@BotFather** → `/newbot` → elegí un nombre.
   Te da un token tipo `123456:ABC-DEF...`
2. Pegá el token en `radar_inmuebles/.env`:
   ```
   TELEGRAM_TOKEN=123456:ABC-DEF...
   ```
3. Abrí tu bot en Telegram y mandale cualquier cosa (un "hola" alcanza).
   Telegram no te dice tu `chat_id` hasta que le escribas.
4. Dejá que el bot lo averigüe solo:
   ```bash
   python -m radar_inmuebles telegram-chatid --guardar
   ```
   Te lo busca, te lo muestra y lo escribe en el `.env`.
5. Probalo:
   ```bash
   python -m radar_inmuebles probar-aviso
   ```

> Si `telegram-chatid` dice que no encontró mensajes: escribile al bot y
> volvé a correrlo. Telegram solo guarda los mensajes pendientes 24 horas.

> **El token es una contraseña.** Vive solo en `radar_inmuebles/.env`, que
> está en el `.gitignore` y nunca se sube. Si alguna vez se te escapa
> (lo pegaste en un chat, en una captura, en un issue), regeneralo con
> `/revoke` en @BotFather y pegá el nuevo en el `.env`.

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

Cuando tengas WhatsApp andando, en `config.yaml` poné:

```yaml
alertas:
  destino: whatsapp
  respaldo: telegram
```

Así el aviso sale por WhatsApp y, si el proveedor se cae, sale por Telegram
solo, sin que toques nada.

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
| MercadoLibre | sitio web (API oficial si hay token) | no |
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
bloquean, y funcionan las 6 fuentes incluidas Zonaprop y Facebook).

### Windows, paso a paso

Hay scripts para que no tengas que usar la terminal. Están en
`radar_inmuebles\despliegue\windows\`.

**1. Instalá Python.** Abrí la Microsoft Store, buscá **Python 3.12** e
instalalo. (Si preferís python.org, al instalar tildá *"Add python.exe to
PATH"*, si no el instalador no lo va a encontrar.)

**2. Bajá el proyecto.** Dos opciones:

- *Con Git* (recomendado, después actualizás con `git pull`): instalá
  [Git para Windows](https://git-scm.com/download/win), abrí PowerShell y:
  ```powershell
  cd $HOME\Documents
  git clone https://github.com/matiascivicoglobal-lab/Workent.git
  ```
- *Sin instalar nada más*: en GitHub, botón verde **Code** → **Download ZIP**,
  y descomprimilo en `Documentos`. Ojo: Windows a veces deja todo dentro de
  una carpeta extra `Workent-main\Workent`; usá la que tiene adentro la
  carpeta `radar_inmuebles`.

**3. Instalá el radar.** Entrá a
`Workent\radar_inmuebles\despliegue\windows\` y hacé **doble clic en
`instalar.bat`**. Tarda unos minutos: instala las dependencias y el navegador
para Zonaprop. Al final te abre el Bloc de notas: pegá ahí tu token de
Telegram en la línea `TELEGRAM_TOKEN=` y guardá con Ctrl+S.

> Si preferís no pelear con el Bloc de notas, cerralo y usá
> **`configurar-token.bat`**: te pide el token, lo valida y lo guarda bien.
> Ojo con las líneas que empiezan con `#`: son comentarios y se ignoran.

**4. Escribile "hola" a tu bot** en Telegram. Sin esto el siguiente paso no
puede encontrar tu chat.

**5. Doble clic en `probar.bat`.** Busca tu chat_id y lo guarda solo, te manda
un mensaje de prueba y prueba los 6 portales. Si te llegó el mensaje a
Telegram, ya está andando.

**6. Doble clic en `radar.bat`.** Queda buscando. Dejá la ventana abierta y
minimizada; se corta cerrándola.

Los otros scripts:

| Archivo | Para qué |
|---|---|
| `configurar-token.bat` | Guarda el token de Telegram sin usar el Bloc de notas |
| `una-pasada.bat` | Una sola búsqueda y cierra, para probar |
| `diagnostico.bat` | Si falla la instalación: revisa red, proxy y DNS |
| `login-facebook.bat` | Iniciás sesión en Facebook una vez, para Marketplace |
| `arrancar-con-windows.bat` | El radar arranca solo al prender la compu |

> Si Windows te muestra *"Windows protegió tu PC"* al abrir un `.bat`, es
> SmartScreen con los archivos bajados de internet: **Más información** →
> **Ejecutar de todas formas**.

### Linux / Mac

```bash
nohup python -m radar_inmuebles watch > radar.log 2>&1 &
```

Con systemd, hay un ejemplo en `despliegue/radar.service`.

**Opción B — Docker** (en tu compu o en un VPS):

```bash
cd radar_inmuebles && docker compose up -d
docker compose logs -f
```

**Opción C — GitHub Actions** (gratis, sin instalar nada, se configura
entero desde el navegador):

Hay dos workflows:

- `.github/workflows/radar.yml` — escanea cada hora y te avisa.
- `.github/workflows/radar-resumen.yml` — un resumen por día a las 19:47,
  para que sepas que sigue vivo aunque no haya aparecido nada.

Pasos:

1. **Cargá los secrets**: *Settings → Secrets and variables → Actions →
   New repository secret*. Necesitás `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`
   (o `CALLMEBOT_APIKEY` si usás WhatsApp).
2. **El workflow tiene que estar en la rama por defecto del repositorio.**
   Esto es lo que más confunde: GitHub **solo ejecuta los cron de la rama
   por defecto**. Si el archivo vive en otra rama, el botón "Run workflow"
   funciona, pero la corrida automática no arranca nunca.
3. Probalo a mano: pestaña *Actions* → *Radar Inmuebles* → *Run workflow*.

Tres límites que conviene saber de entrada:

- **Zonaprop y Facebook no funcionan desde GitHub.** Cloudflare bloquea las
  IPs de los runners y Facebook necesita tu sesión iniciada. Quedan
  MercadoLibre, Argenprop, Properati y RE/MAX, que igual son la mayor parte
  del stock de CABA.
- **La base vive en la caché de Actions.** Ahí se guarda el historial de
  precios y qué avisos ya te mandó. Si la caché se vacía, el bot vuelve a
  empezar y te puede repetir avisos una vez.
- **GitHub apaga los workflows programados tras 60 días sin actividad en el
  repositorio.** Te manda un mail avisando; alcanza con reactivarlos desde
  la pestaña Actions.

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
| `resumen` | Manda el resumen del día (`--sin-enviar` para verlo en pantalla) |
| `probar-aviso` | Manda un mensaje de prueba (`--canal telegram` para probar otro) |
| `login-facebook` | Abre el navegador para iniciar sesión |
| `telegram-chatid` | Encuentra tu chat_id (`--guardar` lo escribe en el `.env`) |

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

## Si algo falla

**`pip` no puede descargar nada (`WinError 10061`, `Max retries exceeded`).**
Probá `diagnostico.bat`. Si `files.pythonhosted.org` resuelve a una dirección
`127.x.x.x`, tu proveedor de internet está bloqueando PyPI con un *walled
garden* (pasa con Telefónica/Movistar). Se arregla cambiando el DNS:

```powershell
# PowerShell como administrador
Set-DnsClientServerAddress -InterfaceAlias "Ethernet" -ServerAddresses 1.1.1.1,8.8.8.8
ipconfig /flushdns
```

**Dice que falta `TELEGRAM_TOKEN` aunque lo pegaste.** La línea del `.env`
probablemente quedó comentada con `#`. Usá `configurar-token.bat`, que lo
escribe bien.

**`telegram-chatid` no encuentra mensajes.** Escribile al bot desde Telegram
y volvé a correrlo. Telegram descarta los mensajes pendientes a las 24 h.

**MercadoLibre devuelve 403.** Desde 2024 la API pública pide token, así que
es lo esperable. El radar lo detecta y pasa solo a leer el sitio web; en el log
vas a ver *"la API de MercadoLibre pide token; paso a leer el sitio web"*. Si
querés usar la API (trae la fecha de publicación real, que el sitio no siempre
muestra), creá una app en developers.mercadolibre.com.ar y poné
`ML_ACCESS_TOKEN` en el `.env`.

**Una fuente devuelve 0 avisos.** Corré `verificar`. Si una sola falla,
seguramente cambió la URL de búsqueda del portal: se ajusta desde
`config.yaml` con `url_template`, sin tocar código.

## Tests

```bash
cd Workent
python -m unittest discover -s radar_inmuebles/tests -t . -p "test_*.py"
```

145 tests, todos offline: parseo de precios argentinos, medianas robustas,
scoring, detección de bajas de precio, dedupe entre portales, armado del mensaje
y el pipeline completo de punta a punta con una fuente falsa.

Los tests usan su propio `tests/config_test.yaml`, así que podés ajustar tu
`config.yaml` sin romperlos. Hay además un test que valida que tu config siga
siendo coherente (rango de precios, teléfono, barrios con valor semilla,
Facebook espaciado).
