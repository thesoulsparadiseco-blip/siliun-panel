# Viabilidad de conexión al FreeStyle Libre

**Paso 3 de la sección 30 del roadmap** ("Viabilidad real de conexión Libre").
Investigación hecha en agosto 2026; el panorama de APIs de Abbott cambia sin
aviso, así que esto hay que revalidarlo antes de escalar más allá de un
piloto con testers informados.

Sigue el orden de prioridad que ya define la sección 20 del roadmap
(`ROADMAP.md`): **A** integración oficial → **B** datos exportados → **C**
conexión directa solo si es legal, segura y necesaria. Ninguna opción
implica tocar el firmware del Libre, tal como exige esa misma sección.

---

## A · Integración oficial

**No encontré un programa de desarrollador self-service de Abbott** (algo
tipo "creá una cuenta, generá una API key") para LibreView/LibreLinkUp. Lo
que sí existe es integración a través de **agregadores de datos de salud**
que ya negociaron acceso con Abbott y revenden el dato normalizado vía su
propia API:

- **Thryve** — API "harmonizada" con acceso a datos de FreeStyle Libre vía
  OAuth2 sobre LibreLink/LibreView, con compliance GDPR/HIPAA/ISO 27001 ya
  resuelto de su lado.
- **Validic** y **Junction** — plataformas similares; Junction expone
  LibreView como "password provider" (el usuario ingresa sus credenciales
  de LibreView dentro del flujo de Junction).

Esto es lo más parecido a "oficial" a lo que puede acceder un desarrollador
independiente hoy: pagar una integración a un tercero, no hablar
directamente con Abbott. Vale la pena pedir cotización/términos a Thryve
antes de escalar el piloto — es el candidato más turnkey — pero **cambia la
arquitectura**: implica que el dato pasa por la nube de un tercero, lo cual
tensiona el principio "Local First" de la sección 21.

## B · Datos sincronizados o exportados

El propio portal **LibreView** (`api.libreview.io`, la web donde
Abbott centraliza los datos del paciente) permite que cualquier usuario
descargue su propio historial (CSV/PDF) desde su cuenta. Sirve para:

- Validar el modelo de datos y el simulador con **datos reales propios**
  sin escribir ningún cliente de API — bajás tu CSV y lo transformás a
  `SignalReading` con `measurement_type=IMPORTED` (ya está en el modelo,
  `physio_sim/models.py`).
- No sirve para un producto en vivo con alertas en tiempo real — es un
  export manual, no un feed continuo.

Es el camino de menor riesgo para el **paso 10** del roadmap ("prueba con
datos reales") mientras se resuelve algo más permanente.

## C · Conexión directa (solo si es legal, segura y necesaria)

Existe un ecosistema activo y bien probado de clientes **no oficiales** que
hablan el mismo API privado que usa la propia app móvil LibreLinkUp de
Abbott — es el mismo camino que lleva usando la comunidad de diabetes
DIY (Nightscout, xDrip+, Loop) desde hace más de una década:

- **Python**: [`libre-link-up-py`](https://github.com/DRFR0ST/libre-link-unofficial-api)
  (activamente mantenido — corre tests automáticos contra el API real cada
  12h), [`pylibrelinkup`](https://pylibrelinkup.readthedocs.io/).
- **TypeScript, listo para usar**:
  [`timoschlueter/nightscout-librelink-up`](https://github.com/timoschlueter/nightscout-librelink-up)
  — un puente Libre→Nightscout desplegable en Render/Heroku/Digital Ocean
  con un `docker run`, sin escribir código propio.
- Soportan multi-región vía variable de entorno (`EU`, `EU2`, `DE`, `FR`,
  `LA`, `US`, etc.) — cubre Latinoamérica y España.
- Modelo de acceso: el dueño del sensor comparte su glucosa vía una
  invitación **LibreLinkUp** (la misma función de "seguidor/cuidador" que
  ya usa Abbott); el cliente no oficial se loguea con ese email/contraseña
  de seguidor y consulta el valor actual + historial cada ~1-5 min.

**Riesgos reales, no cosméticos:**

1. **Términos de uso**: tanto el EULA de LibreLinkUp como los Términos de
   Uso de LibreView prohíben explícitamente "reverse engineer, decompile,
   disassemble... gain access to source code" del producto — exactamente
   lo que hacen estas librerías. Todas se autodescriben como "no oficial",
   "reverse engineered", "usar bajo tu propio riesgo". Abbott no parece
   haber perseguido legalmente a la comunidad DIY en una década, pero eso
   no es una autorización — es tolerancia de facto, revocable.
2. **Fragilidad técnica**: es un API privado no versionado. Abbott lo
   cambió sin aviso en el pasado (ej. la migración a Libre 3 rompió
   integraciones existentes). Para un prototipo/piloto chico es aceptable;
   como dependencia de un producto comercial en escala, no lo es.
3. Ninguna de estas librerías toca el firmware del sensor — el riesgo es
   puramente de términos de servicio de la app/nube, no de seguridad del
   dispositivo médico en sí.

---

## Hallazgo regulatorio nuevo (no estaba en el roadmap original)

La guía revisada de la FDA sobre "General Wellness" (enero 2026) endureció
específicamente la postura sobre glucosa: en el town hall que acompañó la
guía, la FDA señaló que la tecnología CGM **mínimamente invasiva**
(microagujas, el mismo principio que el filamento subcutáneo del Libre)
queda **fuera** del refugio de "wellness, sin aplicación regulatoria" —
incluso con las mismas contraindicaciones y disclaimers que antes alcanzaban
para otros wearables no invasivos (FC, SpO₂ óptico, etc.).

Esto habla del *sensor* en sí (y la sección 22 del roadmap ya descarta
construir un sensor propio, así que no aplica directo). Pero sí es una señal
de que la FDA está mirando la glucosa como parámetro con más lupa que otros
signos vitales — lo cual sube el riesgo regulatorio específicamente de los
**eventos 1 y 2** de la sección 7 (glucosa cayendo rápido, glucosa+FC), más
que el resto de los ocho eventos V1. El lenguaje de la sección 17
("medición, no diagnóstico") sigue siendo la estrategia correcta, pero para
esos dos eventos puntuales conviene una revisión legal específica antes de
salir del piloto Founders — no algo que yo pueda dar por resuelto con
investigación online.

**GDPR**: la glucosa es dato de "categoría especial" (Art. 9 GDPR) — hace
falta consentimiento explícito y específico, no un checkbox genérico de
términos y condiciones. El principio Local First (sección 21) ya construido
ayuda mucho acá (menos dato sale del dispositivo), pero la capa
LibreLinkUp/LibreView en sí ya es un salto a la nube de Abbott que queda
fuera de tu control — hay que nombrarlo en la política de privacidad, no
ocultarlo.

---

## Recomendación concreta

**Para el prototipo y el piloto Founders (sección 26):**

Camino **C**, acotado a título personal — el fundador (u otros testers
informados que generen su propia invitación LibreLinkUp) conectan su
propio Libre vía `libre-link-up-py` o el puente
`nightscout-librelink-up` ya armado. Es exactamente el mismo patrón que
lleva usando la comunidad de diabetes DIY hace 10+ años, no toca firmware,
y no depende de ningún acuerdo comercial para arrancar. Documentar el
riesgo de ToS en el propio README del proyecto (ya lo hice) y no dejar que
se vuelva una dependencia de negocio silenciosa.

**En paralelo, sin bloquear lo anterior:** pedir cotización/términos a
**Thryve** — es el candidato más turnkey para cuando el piloto crezca más
allá de testers que puedan generar su propia invitación LibreLinkUp
manualmente. Ahí sí conviene decidir si vale la pena tensionar el
principio Local First a cambio de compliance ya resuelto.

**Antes de cualquier salida más allá del piloto Founders:** revisión legal
real (no esta investigación) sobre dos cosas puntuales — los eventos 1 y 2
(glucosa) a la luz del endurecimiento de la FDA sobre CGM, y el flujo de
consentimiento GDPR Art. 9 para el dato de glucosa específicamente.

---

## Fuentes

- [LibreLinkUp App End User License Agreement](https://api.libreview.io/document/toullu?lang=en)
- [LibreView Patient/Individual User Terms of Use](https://api.libreview.io/document/toupat?lang=en)
- [DRFR0ST/libre-link-unofficial-api](https://github.com/DRFR0ST/libre-link-unofficial-api)
- [timoschlueter/nightscout-librelink-up](https://github.com/timoschlueter/nightscout-librelink-up)
- [PyLibreLinkUp docs](https://pylibrelinkup.readthedocs.io/)
- [Thryve — Abbott FreeStyle Libre Integration](https://www.thryve.health/features/connections/abbott-freestyle-libre-integration)
- [Troutman Pepper Locke — FDA's 2026 Guidance on General Wellness Devices](https://www.troutman.com/insights/fdas-2026-guidance-on-general-wellness-devices-policy-for-low-risk-devices/)
- [Art. 9 GDPR — Processing of special categories of personal data](https://gdpr-info.eu/art-9-gdpr/)
