# Sistema de llamadas

App de una sola página con dos pestañas:

- **Registro offline** — anota llamadas (contacto, teléfono, tipo, notas) en
  `localStorage` del navegador. No necesita servidor ni conexión; funciona
  incluso abriendo `index.html` directo con `file://`.
- **Video llamada grupal** — video llamada P2P (WebRTC, malla completa) con
  chat de texto grupal en vivo. Esta pestaña sí necesita el servidor de
  señalización (`server.py`), porque dos navegadores no pueden encontrarse
  ni intercambiar audio/video sin un intermediario que les pase las
  direcciones (SDP/ICE).

## Correr localmente

```bash
cd offline-calls
pip install -r requirements.txt
uvicorn server:app --reload --port 8000
```

Abrí `http://localhost:8000` — ahí ya sirve la app completa (las dos
pestañas). Para probar la video llamada con más de una persona, cada una
entra a la misma URL, escribe el mismo nombre de "Sala" y su propio nombre.

## Cómo funciona la video llamada

1. Al entrar a una sala, el navegador se conecta al servidor por WebSocket
   (`/ws/{sala}`) y pide cámara/micrófono.
2. El servidor le informa quién más está en la sala y avisa a los demás que
   alguien nuevo llegó (no guarda nada en disco, solo mientras la sala está
   activa).
3. Cada navegador arma una conexión `RTCPeerConnection` directa con cada uno
   de los demás participantes (topología en malla) usando el servidor solo
   para intercambiar la negociación inicial (offer/answer/ICE candidates).
   El audio y video viajan directo entre navegadores, no por el servidor.
4. El chat de texto se reenvía a todos los participantes de la sala a
   través del mismo WebSocket.

**Limitaciones a tener en cuenta:**
- Usa únicamente un servidor STUN público de Google para NAT traversal. En
  redes muy restrictivas (NAT simétrico, firewalls corporativos estrictos)
  la conexión directa puede fallar — para eso hace falta agregar un
  servidor TURN.
- La malla P2P es apropiada para grupos chicos (hasta 4-6 personas); con
  más participantes cada navegador tiene que subir su video N-1 veces y el
  ancho de banda del cliente se vuelve el cuello de botella.
- El estado de las salas vive en memoria del proceso — si el servidor se
  reinicia, todas las salas activas se cierran.

## Uso desde celular

La interfaz es responsive (probada en simulación de iPhone y Android:
sin scroll horizontal, inputs a 16px para que iOS no haga zoom automático,
botones con área táctil de 44px, y el panel de chat con su propia altura
para que no quede aplastado cuando video y chat se apilan en pantallas
angostas).

⚠️ **Pero ojo con esto:** los navegadores móviles solo dan permiso de
cámara/micrófono en un sitio servido por **HTTPS** (o en `localhost`
mismo). Si abrís la IP local de tu compu por `http://` desde el celular
en la misma wifi, el navegador va a bloquear el permiso y la video
llamada no va a funcionar — el registro offline sí, porque no usa
cámara. Para que la video llamada ande de verdad en celulares:
- Desplegalo en Render (Capítulo 5 / sección de abajo) — te da HTTPS
  automático, o
- Usá un túnel HTTPS temporal mientras desarrollás localmente (por
  ejemplo `ngrok http 8000` o un Cloudflare Tunnel) y abrí esa URL
  `https://...` desde el teléfono.
