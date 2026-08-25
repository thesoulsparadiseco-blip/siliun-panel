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

### ¿Por qué hace falta HTTPS? ¿Y eso no rompe que sea privada/offline?

No son la misma cosa. **HTTPS solo significa que la conexión entre el
navegador y el servidor va cifrada** — es una regla de seguridad que
todos los navegadores de celular imponen para poder usar la cámara o el
micrófono desde una página web (si no, cualquier sitio podría prender tu
cámara sin que te des cuenta). No tiene nada que ver con pasar por
internet ni por un servidor de un tercero: **podés tener HTTPS
completamente local**, dentro de tu propia wifi, sin que un solo byte
salga a internet.

Eso es exactamente lo que arma `generate_cert.py`: un certificado
autofirmado por vos mismo, para tu propia IP de red local. El navegador
del celular va a mostrar un aviso de "conexión no segura" la primera vez
(porque el certificado no lo firmó una autoridad reconocida, no porque
algo esté mal) — lo aceptás una vez y ya funciona.

**Qué tan privada es la app, en concreto:**
- El **video y audio viajan directo entre los dos celulares** (P2P),
  nunca pasan por el servidor.
- Los **mensajes de chat** se reenvían en vivo a través del servidor
  pero **nunca se guardan en disco** — viven solo en la memoria del
  proceso mientras la sala está activa, y desaparecen apenas se cierra.
- El **servidor sos vos**: corre en tu propia computadora, en tu propia
  red, no en la nube de nadie. No hay logs persistentes ni terceros
  involucrados.
- Lo único que **sí queda guardado a propósito** es el registro de
  llamadas offline (`localStorage` del navegador) — es su función:
  llevar un historial. Si no querés que quede rastro de eso, no lo
  uses, o borralo manualmente desde el navegador cuando termines.

Desplegar en Render (más abajo) o usar un túnel tipo ngrok también dan
HTTPS, pero ahí sí el tráfico pasa por la infraestructura de un
tercero — para el objetivo de "no dejar rastro" conviene el modo local
que sigue acá abajo.

### Paso a paso: probarla con dos celulares (100% local, sin internet)

Necesitás: una computadora con Python, y dos celulares conectados a
**la misma red wifi** que esa computadora (no hace falta que esa wifi
tenga internet — puede ser un router sin salida, o un hotspot; alcanza
con que los tres equipos estén en la misma red local).

1. **Instalar dependencias** (una sola vez):
   ```bash
   cd offline-calls
   pip install -r requirements.txt
   ```

2. **Generar el certificado local:**
   ```bash
   python3 generate_cert.py
   ```
   Detecta sola tu IP de red local y muestra algo como:
   ```
   Certificado generado para: 192.168.1.23 (y localhost / 127.0.0.1)
   ...
   Y desde el celular (misma wifi) entrá a: https://192.168.1.23:8443
   ```
   Anotá esa IP y esa URL — las vas a necesitar en el paso 4. Si tu
   compu tiene varias redes (wifi + cable) y detecta la IP equivocada,
   pasásela a mano: `python3 generate_cert.py 192.168.1.23`.

3. **Arrancar el servidor con HTTPS:**
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8443 --ssl-keyfile key.pem --ssl-certfile cert.pem
   ```
   Dejalo corriendo. Si tu computadora tiene firewall (Windows suele
   preguntar la primera vez), aceptá permitir la conexión en redes
   privadas.

4. **Desde el primer celular:** conectate a la misma wifi, abrí el
   navegador y entrá a la URL del paso 2 (`https://TU-IP:8443`). Va a
   aparecer un aviso de "la conexión no es privada" — es esperable
   (ver explicación arriba): tocá **Avanzado → Continuar/Visitar este
   sitio**. Andá a la pestaña **"Video llamada grupal"**, escribí tu
   nombre y un nombre de sala (por ejemplo `equipo`), tocá **"Entrar a
   la sala"** y aceptá el permiso de cámara/micrófono.

5. **Desde el segundo celular:** repetí el paso 4, mismo nombre de
   sala, tu propio nombre.

6. En unos segundos ambos celulares deberían verse y escucharse, con el
   chat funcionando al costado. Si no conecta, revisá la sección de
   solución de problemas abajo.

**Solución de problemas:**
- *No carga la página desde el celular:* confirmá que el celular está
  en la wifi correcta (no en datos móviles) y que es la misma red que
  la computadora. Revisá que no haya un firewall bloqueando el puerto
  8443 en la computadora.
- *Carga pero no pide cámara / da error de permiso:* fijate que la URL
  empiece con `https://` y no `http://`, y que hayas aceptado el aviso
  del certificado.
- *La IP cambió y dejó de andar:* las redes wifi caseras suelen
  reasignar IPs; volvé a correr `python3 generate_cert.py` para
  detectar la IP actual y reiniciá el servidor con esa.
- *Querés acceso fuera de tu wifi (por internet):* eso ya no es 100%
  local — mirá la sección de despliegue en Render más abajo, sabiendo
  que en ese caso el tráfico de señalización pasa por la nube de
  Render (el video/audio P2P sigue sin pasar por ahí).
