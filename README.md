# Siliun Panel

Panel administrativo cloud-ready: backend FastAPI + panel Streamlit,
desplegados en Render, con Cloudflare al frente para DNS/seguridad, y
Webflow como frontend público que embebe/enlaza el panel.

**Nota de diseño:** el spec original pedía "Streamlit (Backend Admin API)"
con endpoints REST (`GET`/`POST /admin/...`). Streamlit no soporta rutas
REST nativas (no maneja verbos HTTP, path params ni headers), así que el
backend real está en FastAPI (`backend/`) y Streamlit (`panel/`) es la UI de
administración que consume esa API — misma arquitectura de 4 capas del
spec, solo que la lógica de "backend" y "UI" están en sus herramientas
correctas.

## Estructura

```
siliun-panel/
├── backend/          # FastAPI — API admin real
│   ├── main.py        # todos los endpoints /admin/*
│   ├── models.py       # esquema UserState + payloads
│   ├── logic.py         # cálculo de resonanceScore / threshold
│   ├── storage.py        # persistencia JSON (swap a Postgres en prod)
│   ├── auth.py             # verificación de Bearer token
│   ├── audit.py             # registro de auditoría
│   ├── notify.py             # envío de mensajes (Discord webhook / stub email)
│   └── organismo_router.py   # endpoints /organismo/* (ver organismo_ia/)
├── organismo_ia/     # Organismo IA Local — motor simbólico + agentes + memoria
│   └── README.md      # detalle de la arquitectura (ver sección 8 abajo)
├── panel/            # Streamlit — UI de administración (7 módulos)
│   └── streamlit_app.py
├── physio_intelligence/  # Physio Intelligence Platform — proyecto independiente (ver sección 9 abajo)
│   └── README.md
├── render.yaml       # blueprint de despliegue (2 servicios + disco)
├── .env.example
└── .gitignore
```

## 1. Correr localmente

```bash
# Backend
cd backend
pip install -r requirements.txt
export SILIUN_ADMIN_TOKEN="dev-token-123"
export DATA_DIR="../data"
uvicorn main:app --reload --port 8000

# Panel (otra terminal)
cd panel
pip install -r requirements.txt
export API_BASE="http://localhost:8000"
export SILIUN_ADMIN_TOKEN="dev-token-123"
streamlit run streamlit_app.py
```

El backend siembra automáticamente el usuario demo de Angelo
(`u_12345`) la primera vez que arranca, así el panel no está vacío.

Probar un endpoint directamente:

```bash
curl -H "Authorization: Bearer dev-token-123" http://localhost:8000/admin/user/u_12345
```

## 2. Endpoints implementados

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/admin/user/:id` | Estado del usuario |
| POST | `/admin/user/:id/state` | Actualiza clarity/rhythm/intention/silence y recalcula resonancia |
| POST | `/admin/user/:id/mark-ready` | Fuerza `user_state_ready = true` |
| POST | `/admin/user/:id/trigger-signal` | Activa señal simbólica (máx. 10/día/admin) |
| POST | `/admin/user/:id/open-malakai` | Abre Malakai manualmente (máx. 5/día/admin) |
| POST | `/admin/user/:id/note` | Guarda nota administrativa |
| POST | `/admin/user/:id/message` | Envía mensaje (Discord webhook) |
| POST | `/admin/audit/log` | Registra acción administrativa manual |
| GET | `/admin/audit/log` | Lee el log de auditoría |
| GET | `/admin/users` | Lista todos los usuarios |
| POST | `/admin/user` | Crea un usuario nuevo |
| GET | `/health` | Health check (sin auth) |

Todas las rutas `/admin/*` requieren:
```
Authorization: Bearer <SILIUN_ADMIN_TOKEN>
X-Admin-Id: <nombre-del-admin>   (opcional, para el log de auditoría)
```

## 3. Desplegar en Render

**Opción A — Blueprint (recomendado):**
1. Subí este repo a GitHub.
2. En Render: New → Blueprint → seleccioná el repo. Render lee `render.yaml`
   y crea los dos servicios (`siliun-backend`, `siliun-panel-ui`) más el
   disco persistente para los datos.
3. Completá los env vars marcados `sync: false` (`SILIUN_ADMIN_TOKEN`,
   `DISCORD_WEBHOOK_URL`) en el dashboard de Render — son secretos, no van
   en el repo.
4. Una vez desplegado el backend, copiá su URL pública y actualizá
   `API_BASE` en el servicio `siliun-panel-ui`.

**Opción B — manual:** creá dos Web Services en Render apuntando a
`backend/` y `panel/` respectivamente, usando los `buildCommand`/`startCommand`
de `render.yaml` como referencia.

⚠️ **Persistencia:** el plan free de Render sin disco pierde el filesystem
en cada redeploy. `render.yaml` ya monta un disco de 1GB en `DATA_DIR` para
el backend. Para producción real (más de un puñado de usuarios o alta
disponibilidad), migrá `storage.py` a Postgres (Render lo ofrece gratis) —
las funciones (`get_user`, `upsert_user`, etc.) están aisladas justamente
para que ese cambio no toque el resto del código.

## 4. Configurar Cloudflare (sección 6 del spec)

1. **DNS:** apuntá tu dominio/subdominio a la URL de Render del backend
   (CNAME) y del panel si tiene dominio propio.
2. **SSL/TLS:** modo Full (o Full Strict si tenés certificado válido en
   origen), activar HSTS, forzar TLS 1.3.
3. **Firewall Rule** — bloquear `/admin/*` salvo:
   - IPs autorizadas, o
   - request con header `Authorization: Bearer <SILIUN_ADMIN_TOKEN>`

   Regla de ejemplo (Cloudflare Firewall Rules, expresión):
   ```
   (http.request.uri.path contains "/admin/") and not (http.request.headers["authorization"][0] eq "Bearer TU_TOKEN_AQUI")
   ```
   (Ojo: exponer el token en una regla de Cloudflare es legible por
   cualquiera con acceso al dashboard — para mayor seguridad, restringí por
   IP en vez de por header, o usá Cloudflare Access delante del panel.)
4. **Rate Limiting:** Cloudflare Rate Limiting Rules como capa adicional
   sobre los límites ya aplicados en el backend (5 aperturas Malakai/día,
   10 señales/día por admin).
5. **Edge Rules:** cachear contenido público, `Cache-Control: no-store`
   para todo `/admin/*`, redirect `/panel` → `/siliun/panel` si aplica.
6. **KV (opcional):** solo si querés logs ultra-rápidos en el edge; el
   backend ya lleva su propio audit log en `data/audit_log.jsonl`.

## 5. Conectar el frontend Webflow

En la página privada `/siliun/panel`, el embed del pseudofront debe apuntar
a la URL pública del servicio `siliun-panel-ui` de Render (o incrustarla en
un iframe). Protegé esa página con Memberstack para que solo admins la vean
— eso es aparte de la auth del backend, no la reemplaza.

## 6. Tu agente personal (`/agent`, conectado a Claude)

Además del panel admin, el backend sirve un agente personal en
`https://<tu-backend>.onrender.com/agent/` — una versión de "369 · Sistema
Tesla" que, a diferencia del archivo local original, habla con la API real
de Claude en vez de responder solo con frases fijas.

**Cómo queda protegido:** el navegador nunca ve tu clave de Anthropic. El
frontend (`backend/static/agent/`) le pide texto a `POST /api/agent/chat`
en el propio backend, mandando tu `AGENT_TOKEN` personal en el header
`Authorization`; el backend es quien llama a Anthropic con
`ANTHROPIC_API_KEY` guardada como variable de entorno. `AGENT_TOKEN` es
un secreto distinto de `SILIUN_ADMIN_TOKEN` — uno abre el panel admin,
el otro abre tu agente.

**Setup:**
1. Generá una API key en [console.anthropic.com](https://console.anthropic.com)
   y un token personal largo y aleatorio (para `AGENT_TOKEN`).
2. En Render, completá `ANTHROPIC_API_KEY` y `AGENT_TOKEN` en el servicio
   `siliun-backend` (son `sync: false`, no van en el repo).
3. Abrí `/agent/` desde el navegador de tu móvil y de tu ordenador. La
   primera vez te va a pedir el token personal (ícono ⚙ arriba a la
   derecha) — se guarda solo en ese dispositivo (`localStorage`), no en
   el servidor.
4. **Instalarlo como app:** en el móvil (Chrome/Safari) usá "Añadir a
   pantalla de inicio"; en el ordenador (Chrome/Edge) el icono de
   instalar aparece en la barra de direcciones. Es una PWA (`manifest.json`
   + service worker), así que abre en su propia ventana sin barra del
   navegador, en ambos dispositivos.

**Límites que hay que conocer:**
- `AGENT_DAILY_LIMIT` (por defecto 300 mensajes/día) frena el gasto de la
  API si el token se filtra — ajustalo en Render si lo necesitás.
- **Activación por voz o 3 aplausos, solo en primer plano.** El botón
  "Activar con voz / 3 aplausos" pide permiso de micrófono y, mientras esa
  pestaña siga abierta y visible, detecta 3 palmadas seguidas (análisis de
  amplitud con Web Audio API) o la palabra clave "agente" (reconocimiento
  de voz continuo) para abrir el chat sin tocar la pantalla — funciona
  igual en el móvil y en el ordenador. **No puede correr con la pantalla
  bloqueada ni con la pestaña en segundo plano**: ningún navegador permite
  eso desde una página web, ni siquiera instalada como PWA — se pausa sola
  al ocultarse y se reanuda al volver. El reconocimiento de voz continuo
  envía audio a los servidores de Google (como el resto de la Web Speech
  API), así que requiere conexión.
- Sin token configurado, o sin red, el agente cae de vuelta a su base de
  conocimiento local sobre 369/Tesla/Cábala (la misma del archivo
  original) — sigue siendo útil offline, solo que sin IA real.

## 7. Organismo IA Local (`/organismo/*`, autosuficiente)

Implementación del documento *Organismo IA Local · Arquitectura
Ejecutable*: un motor simbólico (Tesla 3-6-9, elementos, atractor/
detractor) que coordina 9 agentes internos (Solkin, Vitalion, Almir,
Nodar, Helion, Paradion, Synar, Arkhon, Jakhar) sobre una capa de
memoria propia (JSON + sqlite, sin dependencias nuevas). Vive en
`organismo_ia/` — el detalle completo (qué corre aquí vs. qué requiere
el cliente móvil del spec original) está en `organismo_ia/README.md`.

**Interfaz web:** `https://<tu-backend>.onrender.com/organismo-app/` — una
PWA (misma técnica que `/agent`: `manifest.json` + service worker,
instalable en móvil y ordenador) donde se ve el organismo "vivo": un
pentágono con los 5 elementos que se ilumina según el elemento activo,
la puerta Tesla al centro, los agentes que intervinieron como chips, y
dictado/lectura por voz. Pide el mismo token que `/agent` (se guarda una
sola vez, se comparte entre ambas apps) y un selector AUTO/ES/EN para
forzar el idioma si no querés que se autodetecte turno a turno.

Usa la misma auth que `/agent` (`AGENT_TOKEN`). El idioma se autodetecta
si no se indica (español de España por defecto, inglés si el texto lo
sugiere) — ver `organismo_ia/i18n/`:

```bash
curl -X POST http://localhost:8000/organismo/invoke \
  -H "Authorization: Bearer $AGENT_TOKEN" -H "Content-Type: application/json" \
  -d '{"input": "Quiero sanar mi cuerpo y encontrar estabilidad", "user_id": "u_12345"}'

# o forzando idioma:
curl -X POST http://localhost:8000/organismo/invoke \
  -H "Authorization: Bearer $AGENT_TOKEN" -H "Content-Type: application/json" \
  -d '{"input": "I want to heal my body", "user_id": "u_12345", "locale": "en"}'
```

**Independiente a propósito:** a diferencia de `/agent` (que sí es un
asistente conectado a Claude, por diseño), `/organismo/invoke` nunca
llama a Claude ni a ninguna otra IA externa — la manifestación final
siempre sale del template determinista que integra las voces de los
agentes, aunque `ANTHROPIC_API_KEY` esté configurada para `/agent`.
Autosuficiente es el comportamiento real, no un fallback (sección 1 del
spec original). Añadir un idioma nuevo no requiere tocar el motor — ver
la sección "Idiomas" de `organismo_ia/README.md`.

**Núcleo IA local (`core_llm` real, capa 5.1 del spec):** el backend
clasifica (elemento/puerta/agentes) pero no genera texto libre — eso es
determinista a propósito. Para que el organismo *responda* de verdad en
vez de solo clasificar, sin depender de ningún servidor externo,
`/organismo-app` puede activar un modelo de lenguaje pequeño que corre
**en el propio navegador** vía WebGPU ([WebLLM](https://github.com/mlc-ai/web-llm),
cargado desde CDN como módulo ES). Es opt-in (botón "Activar" en el
encabezado, no arranca solo) porque implica bajar unos cientos de MB la
primera vez; se cachea en el dispositivo, así que las visitas
siguientes no vuelven a descargar. La clasificación del backend se le
pasa como contexto al modelo para que la respuesta esté informada por
el elemento/agentes activos, en vez de repetir un template fijo.
Requiere un navegador con WebGPU (Chrome/Edge de escritorio y Android
andan bien; Safari/iOS todavía tiene soporte limitado) — sin eso, o si
falla la carga, el organismo sigue funcionando con el motor determinista
de siempre, sin romperse.

"Aprende" ahí significa memoria de la conversación guardada en
`localStorage` del navegador (los últimos intercambios se le pasan de
contexto al modelo en cada turno) — no reentrena los pesos del modelo,
eso sería otro proyecto. Correr este mismo modelo en el servidor
(Render) en vez del navegador no es viable en el plan free (512MB de
RAM no alcanza ni para un modelo chico cuantizado).

## 8. Checklist de arranque

- [x] Backend FastAPI con todos los endpoints del spec
- [x] Modelo de datos / esquema de usuario
- [x] Cálculo de resonancia + threshold configurable
- [x] Rate limiting (Malakai, señales)
- [x] Audit log
- [x] Panel Streamlit con los 7 módulos
- [x] `render.yaml` listo para blueprint deploy
- [x] Agente personal `/agent` conectado a Claude (proxy server-side, PWA)
- [x] Organismo IA Local (`/organismo/*`): engines, 9 agentes, memoria — ver sección 7
- [x] Núcleo IA local opt-in en `/organismo-app` (WebLLM, corre en el navegador) — ver sección 7
- [x] Configurar `SILIUN_ADMIN_TOKEN` y `AGENT_TOKEN` reales en Render
- [ ] Configurar `ANTHROPIC_API_KEY` en Render (solo para `/agent` — `/organismo` no la usa)
- [ ] Apuntar DNS en Cloudflare + firewall rules
- [ ] Conectar `DISCORD_WEBHOOK_URL` para notificaciones
- [ ] Embeber el panel en la página Webflow `/siliun/panel`
- [ ] Migrar `storage.py` a Postgres antes del piloto con usuarios reales
- [ ] Piloto Founders (5–10 usuarios, sesión 23 julio)

## 9. Physio Intelligence Platform (`physio_intelligence/`, proyecto independiente)

Vive en este mismo repo por conveniencia, pero **no tiene relación** con
Siliun Panel — es un producto distinto: una plataforma que aprende el
comportamiento fisiológico habitual de una persona (glucosa, FC,
temperatura, movimiento, ambiente) y detecta cuándo se desvía de su propio
patrón. El roadmap completo (V1–V3) está en
`physio_intelligence/docs/ROADMAP.md`.

Lo que hay implementado ahora es el MVP de 7 días de ese roadmap: un
**simulador fisiológico** sin sensores reales que ejercita de punta a punta
el Personal Baseline Model, un **Cardiac Agent** (FC, IBI, HRV) y un
**Metabolic Agent** (glucosa + pendiente), y el Fusion Engine (reglas
cross-dominio + persistencia, sin IA) con su caja negra de eventos
(±60 min), sobre los 8 eventos definidos en el documento — detalle
completo en `physio_intelligence/README.md`.

```bash
cd physio_intelligence
python -m physio_sim.cli                  # corre los 9 escenarios sintéticos
pip install -r requirements-dev.txt && pytest   # 16 tests
```
