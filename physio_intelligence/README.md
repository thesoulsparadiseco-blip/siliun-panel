# Physio Intelligence Platform

Plataforma de Inteligencia Fisiológica — el roadmap completo (V1–V3) está en
[`docs/ROADMAP.md`](docs/ROADMAP.md). Este repo implementa los primeros
pasos concretos de esa hoja de ruta: el **paso 5 de la sección 30**
(simulador fisiológico, el **MVP de 7 días de la sección 23**), los
**pasos 6 y 7** (primer agente cardiovascular y metabólico, sección 6), el
**paso 9** (primera alerta en reloj, sección 3), y la investigación del
**paso 3** (viabilidad real de conexión al Libre — ver
[`docs/LIBRE_CONNECTIVITY.md`](docs/LIBRE_CONNECTIVITY.md)).

## Qué es esto

Un simulador que genera señales fisiológicas sintéticas — sin sensores
reales — y las hace pasar por el mismo pipeline que correrá el producto
final:

```text
escenario sintético
        ↓
Personal Baseline Model   (media/desviación por señal + contexto, sección 10)
        ↓
   ┌────────────────┬──────────────────┐
   ▼                ▼                  │
Cardiac Agent   Metabolic Agent        │   (sección 6 — cada uno mira solo su dominio)
FC, IBI, HRV    glucosa + pendiente    │
   └────────────────┴──────────────────┘
                     ↓
              Fusion Engine   (reglas cross-dominio + persistencia, sección 6 y 8)
                     ↓
              8 eventos V1     (sección 7)
                ↓         ↓
         Black Box   Action Engine   (±60 min · sección 11 / RELOJ · sección 3)
                            ↓
                     WatchAlert → reloj
```

Cardiac y Metabolic son los dos primeros "Agentes Fisio" de la sección 6:
cada uno mira solo su propio dominio contra el baseline personal y decide
sus propios eventos — Cardiac: FC alta/baja en reposo, recuperación anómala
tras ejercicio; Metabolic: glucosa descendiendo rápidamente. El Fusion
Engine los consulta a ambos como a cualquier otro agente y añade únicamente
lo que es genuinamente cross-dominio — la combinación glucosa+FC y la
anomalía multisensor, que por definición ningún agente individual puede ver
por sí solo.

El Action Engine (sección 3) traduce cada evento confirmado en una
`WatchAlert`: el mensaje que ya redactó el propio evento (medición +
inferencia, nunca diagnóstico — sección 17) más las opciones de feedback
humano relevantes para ese evento (sección 12, ej.: "Mareo", "Palpitaciones",
"Sed" para una caída de glucosa). Sin reloj real todavía, `WatchChannel` es
un canal en memoria que solo colecciona lo que se hubiera entregado — el
mismo espíritu que el resto del simulador: probar el contrato de punta a
punta antes de tener hardware.

Existe para responder la pregunta de la sección 27 antes de tener ningún
hardware: *¿recibimos señales, las contextualizamos, creamos un baseline y
detectamos un evento?* — sin esperar a resolver Android/Wear OS/CGM.

No hay redes neuronales ni modelos de IA: es reglas + estadística sobre el
baseline personal, tal como pide la sección 13 ("Sin redes neuronales
complejas").

## Señales simuladas (núcleo V1, sección 4)

Glucosa, frecuencia cardíaca, temperatura cutánea, movimiento, temperatura
ambiental y humedad — las seis entradas que pide literalmente la sección
23 — más IBI y HRV, que la sección 6 asigna al Cardiac Agent
("FC, HRV, IBI, PPG y ECG puntual"). El IBI se deriva de la FC
(60000 / FC + ruido, son el mismo canal cardíaco visto de dos formas); la
HRV es una señal independiente. PPG bruto y ECG bajo demanda quedan fuera
de este simulador a propósito: son señales de forma de onda, no un escalar
por tick como el resto del modelo de datos, y el propio roadmap los sitúa
en V2 (sección 14).

## Los 8 eventos (sección 7)

1. Glucosa descendiendo rápidamente
2. Glucosa descendiendo + FC aumentando
3. FC inusualmente alta en reposo
4. FC inusualmente baja respecto al patrón personal
5. Carga térmica elevada
6. Recuperación inusual después de ejercicio
7. Caída + inmovilidad
8. Anomalía multisensor no clasificada

Cada uno tiene su propio escenario sintético en `physio_sim/scenarios.py`,
más un escenario `normal_day` sin anomalías que sirve de control (para
comprobar que el motor no genera falsos positivos).

## Correr los escenarios

```bash
python -m physio_sim.cli                  # los 9 escenarios
python -m physio_sim.cli hr_high_at_rest   # uno solo
```

Salida de ejemplo (`fall_immobility`):

```text
=== fall_immobility ===
Ticks simulados: 71
Eventos detectados: 3
  [08:05] ALERTA     Caída + inmovilidad — Impacto de 3.5g seguido de 5 min sin movimiento.
  [08:06] ALERTA     Caída + inmovilidad — Impacto de 3.5g seguido de 6 min sin movimiento.
  [08:07] ALERTA     Caída + inmovilidad — Impacto de 3.5g seguido de 7 min sin movimiento.
Alertas entregadas al reloj: 3
  ej.: 🔴 "Caída + inmovilidad" — feedback: [Estoy bien, Dolor, Mareo, Otro]
```

(El evento se re-confirma cada pocos ticks mientras la condición se
mantiene — es intencional: el sistema sigue "viendo" la anomalía, no la
reporta una sola vez y se calla. Ajustar ese ritmo de re-alerta es un
parámetro de tuning para V1 real, no algo que decida este simulador.)

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

42 tests. Verifican, escenario por escenario, que:
- el baseline no puntúa desviaciones hasta tener suficientes muestras
  (`MIN_SAMPLES_FOR_BASELINE`, sección 10);
- el Cardiac Agent aísla FC/IBI/HRV correctamente, solo dispara "FC alta"
  en contexto de reposo, y detecta la transición ejercicio→reposo para la
  regla de recuperación (`tests/test_cardiac_agent.py`, sin pasar por el
  Fusion Engine);
- el Metabolic Agent solo dispara con una pendiente sostenida (no con
  ruido plano), respeta la ventana de persistencia, y se puede suprimir
  cuando el Fusion Engine ya explicó la caída vía el evento cross-dominio
  (`tests/test_metabolic_agent.py`, también sin Fusion Engine);
- cada uno de los 8 eventos se dispara en su escenario correspondiente a
  través del pipeline completo;
- el día normal no genera ningún evento (cero falsos positivos) ni ninguna
  alerta de reloj;
- la caja negra abre un episodio con ventana "antes" por cada evento, lo
  cierra recién a los 60 min de después (ni un minuto antes), y
  `add_feedback` adjunta la respuesta humana al episodio correcto sin
  filtrarse a otros (`tests/test_blackbox.py`, sección 11 y 12);
- el Action Engine nunca reescribe el mensaje del evento (medición +
  inferencia, nunca diagnóstico), cada tipo de evento tiene sus opciones de
  feedback ("Estoy bien" primero, "Otro" al final, sin duplicados), y en una
  corrida completa cada evento detectado llega exactamente una vez al reloj
  (`tests/test_action_engine.py`).

## Estructura

```text
physio_sim/
  models.py       # SignalReading + los 5 tipos de medición (sección 19)
  baseline.py     # Personal Baseline Model, Welford online por (señal, contexto)
  history.py      # SignalHistory: ventana deslizante + pendiente, compartida por agentes y Fusion Engine
  agents/
    cardiac.py     # Cardiac Agent: FC, IBI, HRV contra el baseline (sección 6)
    metabolic.py   # Metabolic Agent: glucosa + pendiente contra el baseline (sección 6)
  fusion.py       # Fusion Engine: reglas cross-dominio + persistencia (secciones 6 y 8)
  events.py       # EventType (8), SystemState (HABITUAL/CAMBIO/COMPROBAR/ALERTA)
  action_engine.py # Action Engine: Event -> WatchAlert + feedback (sección 3, paso 9)
  blackbox.py     # Caja negra ±60 min (sección 11)
  scenarios.py    # 9 escenarios sintéticos (los 8 eventos + control)
  simulator.py    # orquesta escenario → baseline → agentes → fusión → reloj → caja negra
  cli.py          # punto de entrada de línea de comandos
tests/
  test_baseline.py
  test_cardiac_agent.py
  test_metabolic_agent.py
  test_fusion_events.py
  test_action_engine.py
  test_blackbox.py
docs/
  ROADMAP.md      # documento maestro completo (V1–V3)
```

## Qué NO es esto

No es la app Android/Wear OS de la sección 18, no lee ningún sensor real
(Libre, Galaxy Watch, BLE), no hay reloj real recibiendo notificaciones, y
no persiste nada — cada corrida es en memoria y desde cero. Es
deliberadamente así: el objetivo del MVP de 7 días es validar el *pipeline
de decisión*, no el hardware. El siguiente paso natural (sección 30,
paso 10) es sustituir `scenarios.py` por datos reales de un smartwatch y
un CGM, y `WatchChannel` por la entrega real a Wear OS, manteniendo
`baseline.py`, `fusion.py`, `agents/`, `action_engine.py` y `blackbox.py`
sin cambios de fondo.

## Próximos pasos (sección 30)

1. ~~Nombre provisional del proyecto~~ — `physio-intelligence-platform`
2. Hardware exacto del prototipo
3. ~~Viabilidad real de conexión Libre~~ — investigado, ver [`docs/LIBRE_CONNECTIVITY.md`](docs/LIBRE_CONNECTIVITY.md); recomendación: camino C (API no oficial, ej. `libre-link-up-py`) acotado al piloto Founders, evaluando Thryve en paralelo para escalar
4. Arquitectura Android/Wear OS
5. ~~Simulador fisiológico~~ — **este repo**
6. ~~Primer agente cardiovascular~~ — **`physio_sim/agents/cardiac.py`**, sobre datos sintéticos; falta conectarlo a un smartwatch real
7. ~~Primer agente metabólico~~ — **`physio_sim/agents/metabolic.py`**, sobre datos sintéticos; falta conectarlo a un CGM real
8. ~~Fusion Engine sobre datos reales~~ — construido aquí (sección 8 arriba); falta conectarlo a datos reales
9. ~~Primera alerta en reloj~~ — **`physio_sim/action_engine.py`**, contrato `Event → WatchAlert` probado de punta a punta con `WatchChannel` simulado; falta un reloj real que la reciba
10. Prueba con datos reales
