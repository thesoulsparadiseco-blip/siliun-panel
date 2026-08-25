# Physio Intelligence Platform

Plataforma de Inteligencia Fisiológica — el roadmap completo (V1–V3) está en
[`docs/ROADMAP.md`](docs/ROADMAP.md). Este repo implementa el primer paso
concreto de esa hoja de ruta: el **paso 5 de la sección 30** (simulador
fisiológico), que a su vez es el **MVP de 7 días de la sección 23**.

## Qué es esto

Un simulador que genera señales fisiológicas sintéticas — sin sensores
reales — y las hace pasar por el mismo pipeline que correrá el producto
final:

```text
escenario sintético
        ↓
Personal Baseline Model   (media/desviación por señal + contexto, sección 10)
        ↓
Fusion Engine              (reglas + persistencia, sección 6 y 8)
        ↓
8 eventos V1                (sección 7)
        ↓
Black Box                  (±60 min por evento, sección 11)
```

Existe para responder la pregunta de la sección 27 antes de tener ningún
hardware: *¿recibimos señales, las contextualizamos, creamos un baseline y
detectamos un evento?* — sin esperar a resolver Android/Wear OS/CGM.

No hay redes neuronales ni modelos de IA: es reglas + estadística sobre el
baseline personal, tal como pide la sección 13 ("Sin redes neuronales
complejas").

## Señales simuladas (núcleo V1, sección 4)

Glucosa, frecuencia cardíaca, temperatura cutánea, movimiento, temperatura
ambiental y humedad — las seis entradas que pide literalmente la sección 23.

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

Los tests verifican, escenario por escenario, que:
- el baseline no puntúa desviaciones hasta tener suficientes muestras
  (`MIN_SAMPLES_FOR_BASELINE`, sección 10);
- cada uno de los 8 eventos se dispara en su escenario correspondiente;
- el día normal no genera ningún evento (cero falsos positivos);
- la caja negra abre un episodio con ventana "antes" por cada evento
  (sección 11).

## Estructura

```text
physio_sim/
  models.py     # SignalReading + los 5 tipos de medición (sección 19)
  baseline.py   # Personal Baseline Model, Welford online por (señal, contexto)
  fusion.py     # Fusion Engine: las 8 reglas + persistencia (secciones 6 y 8)
  events.py     # EventType (8), SystemState (HABITUAL/CAMBIO/COMPROBAR/ALERTA)
  blackbox.py   # Caja negra ±60 min (sección 11)
  scenarios.py  # 9 escenarios sintéticos (los 8 eventos + control)
  simulator.py  # orquesta escenario → baseline → fusión → caja negra
  cli.py        # punto de entrada de línea de comandos
tests/
  test_baseline.py
  test_fusion_events.py
docs/
  ROADMAP.md    # documento maestro completo (V1–V3)
```

## Qué NO es esto

No es la app Android/Wear OS de la sección 18, no lee ningún sensor real
(Libre, Galaxy Watch, BLE), y no persiste nada — cada corrida es en
memoria y desde cero. Es deliberadamente así: el objetivo del MVP de 7
días es validar el *pipeline de decisión*, no el hardware. El siguiente
paso natural (sección 30, pasos 6–8) es sustituir `scenarios.py` por datos
reales de un agente cardiovascular y uno metabólico, manteniendo
`baseline.py`, `fusion.py` y `blackbox.py` sin cambios.

## Próximos pasos (sección 30)

1. ~~Nombre provisional del proyecto~~ — `physio-intelligence-platform`
2. Hardware exacto del prototipo
3. Viabilidad real de conexión Libre
4. Arquitectura Android/Wear OS
5. ~~Simulador fisiológico~~ — **este repo**
6. Primer agente cardiovascular (datos reales de un smartwatch)
7. Primer agente metabólico (datos reales de un CGM)
8. Fusion Engine sobre datos reales (ya construido aquí, sección 8 arriba)
9. Primera alerta en reloj
10. Prueba con datos reales
