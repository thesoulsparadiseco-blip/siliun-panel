# Plataforma de Inteligencia Fisiológica

## Documento Maestro · Roadmap V1–V3

## 1. Objetivo real

Construir una plataforma personal capaz de reunir señales procedentes de diferentes sensores, aprender el comportamiento habitual de una persona, detectar desviaciones relevantes, contextualizarlas y generar información o avisos útiles.

El producto no estará ligado a un único fabricante.

FreeStyle Libre será inicialmente la fuente de glucosa, pero la arquitectura deberá admitir otros CGM y wearables en el futuro.

---

# 2. Concepto central

La evolución del producto será:

**MEDIR → ENTENDER → ANTICIPAR → COMPROBAR → ACTUAR → APRENDER**

No buscamos simplemente mostrar métricas.

Buscamos responder:

**¿Qué está ocurriendo en mi cuerpo?**

**¿Es habitual para mí?**

**¿Qué otras señales están cambiando?**

**¿Hacia dónde parece evolucionar?**

**¿Necesito prestar atención?**

---

# 3. Arquitectura conceptual definitiva

```text
                           PERSONA
                              │
         ┌────────────────────┼─────────────────────┐
         │                    │                     │
         ▼                    ▼                     ▼
       CGM                SMARTWATCH             ENTORNO
      glucosa             corazón/piel          temperatura
                           movimiento             humedad
                           sueño                  CO₂ futuro
                           respiración            etc.
         │                    │                     │
         └────────────────────┼─────────────────────┘
                              ▼
                        SMARTPHONE
                              │
                       BODY DATA HUB
                              │
                  PERSONAL BASELINE MODEL
                              │
                        AGENTES FISIO
                              │
                        FUSION ENGINE
                              │
                    PHYSIOLOGICAL RADAR
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
              DETECTAR     PREDECIR     COMPROBAR
                 │            │            │
                 └────────────┼────────────┘
                              ▼
                         ACTION ENGINE
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
           RELOJ            MÓVIL           ENTORNO
                              │
                              ▼
                           USUARIO
                              │
                           feedback
                              │
                              └────────────► APRENDIZAJE
```

---

# 4. Las señales

## Núcleo V1

| Área           | Señales                                                  |
| -------------- | -------------------------------------------------------- |
| Metabolismo    | glucosa, pendiente, aceleración                          |
| Cardiovascular | FC, IBI, HRV                                             |
| Piel           | temperatura cutánea                                      |
| Movimiento     | aceleración, actividad, reposo                           |
| Sueño          | dormido/despierto y contexto nocturno                    |
| Respiratorio   | frecuencia respiratoria si está disponible               |
| Oxigenación    | SpO₂ si está disponible                                  |
| Ambiente       | temperatura + humedad                                    |
| Hidratación    | agua registrada + carga hídrica estimada                 |
| Humano         | síntomas, comidas, café, ejercicio, medicación, feedback |

---

# 5. Las tres capas térmicas e hídricas

Quedan definitivamente incorporadas.

### CAPA 1 · Temperatura cutánea

Medida por wearable compatible.

Se utilizará principalmente como desviación respecto al patrón individual.

### CAPA 2 · Temperatura + humedad ambiental

Obtenida inicialmente mediante sensor BLE externo o fuente compatible.

Permite contextualizar:

* pulso;
* sudor;
* ejercicio;
* temperatura cutánea;
* recuperación.

### CAPA 3 · Estado hídrico estimado

Combina:

* actividad;
* ambiente;
* sudor estimado;
* FC;
* agua ingerida;
* temperatura;
* BIA futura.

Será una **estimación**, no una medición clínica de deshidratación.

---

# 6. Agentes especializados

## Metabolic Agent

Glucosa, tendencias, comidas y ejercicio.

## Cardiac Agent

FC, HRV, IBI, PPG y ECG puntual cuando esté disponible.

## Thermal Agent

Temperatura cutánea + temperatura y humedad ambientales.

## Hydration Agent

Actividad + sudor + ambiente + agua + señales corporales.

## Respiratory Agent

Respiración + SpO₂ + contexto.

## Sleep Agent

FC + HRV + temperatura + respiración + glucosa + movimiento nocturno.

## Movement Agent

Reposo, caminar, ejercicio, caída e inmovilidad.

## Environment Agent

Temperatura, humedad y posteriormente CO₂, partículas, VOC, ruido, etc.

## Human Agent

Síntomas y contexto indicado por la persona.

## Memory Agent

Busca episodios similares anteriores.

## Prediction Agent

Estudia la posible trayectoria futura.

## Confirmation Agent

Solicita otra medición cuando la información sea insuficiente.

## Safety Agent

Evita conclusiones cuando los sensores son poco fiables o están desconectados.

## Fusion Agent

Integra todo y decide si existe un cambio relevante.

---

# 7. Los primeros eventos que reconoceremos

Para V1 no intentaremos reconocer decenas de situaciones.

Empezaremos con ocho:

1. Glucosa descendiendo rápidamente.
2. Glucosa descendiendo + FC aumentando.
3. FC inusualmente alta en reposo.
4. FC inusualmente baja respecto al patrón personal.
5. Carga térmica elevada.
6. Recuperación inusual después de ejercicio.
7. Caída + inmovilidad.
8. Anomalía multisensor no clasificada.

El octavo es especialmente importante porque permite detectar:

> **"Algo está ocurriendo de forma diferente a tu comportamiento habitual."**

sin intentar diagnosticar su causa.

---

# 8. Flujo de decisión

Cada posible evento recorrerá:

```text
DATO
  ↓
¿ES FIABLE?
  ↓
CONTEXTO
  ↓
BASELINE PERSONAL
  ↓
DESVIACIÓN
  ↓
VELOCIDAD
  ↓
PERSISTENCIA
  ↓
OTRAS SEÑALES
  ↓
EXPLICACIONES ALTERNATIVAS
  ↓
CONFIRMACIÓN
  ↓
ACCIÓN
```

---

# 9. Estados del sistema

No utilizaremos únicamente NORMAL / ALARMA.

### 🟢 HABITUAL

Sin cambios relevantes.

### 🟡 CAMBIO

Algo se está alejando del patrón.

### 🟠 COMPROBAR

La desviación persiste o varias señales coinciden.

### 🔴 ALERTA

Evento prioritario conforme a reglas previamente definidas y validadas.

---

# 10. Personal Baseline

Este es el verdadero corazón del producto.

El sistema aprenderá cómo se comporta normalmente cada usuario según:

* hora;
* sueño;
* reposo;
* ejercicio;
* comida;
* temperatura;
* humedad;
* historial reciente;
* contexto.

No existirá una sola normalidad.

Habrá:

**normal durmiendo**

**normal caminando**

**normal después de comer**

**normal entrenando**

**normal con calor**

etc.

---

# 11. Caja negra fisiológica

El sistema mantendrá un buffer temporal.

Cuando detecte un evento guardará automáticamente:

**60 minutos antes**

*

**evento**

*

**60 minutos después**

Incluyendo las señales disponibles.

Esto permitirá reconstruir lo ocurrido y, posteriormente, detectar precursores.

---

# 12. Feedback humano

Después de determinados eventos el usuario podrá responder:

* estoy bien;
* mareo;
* palpitaciones;
* calor;
* sed;
* falta de aire;
* dolor;
* estrés;
* otro.

Esta información se guarda junto al episodio.

Así conseguimos:

**datos objetivos + contexto + sensación subjetiva.**

---

# 13. V1 · PRODUCTO CONSTRUIBLE AHORA

## Objetivo

Demostrar que diferentes sensores pueden integrarse en una única línea temporal y detectar cambios personales útiles.

## Hardware

**Android**

**Galaxy Watch compatible**

**FreeStyle Libre**

**sensor BLE temperatura/humedad**

## Datos

Glucosa
FC
IBI / HRV
temperatura cutánea
movimiento
sueño
temperatura ambiental
humedad
feedback humano

## Inteligencia

Reglas.

Estadística.

Baseline personal.

Fusión multisensor.

Sin redes neuronales complejas.

## Producto

App Android.

App Wear OS.

Dashboard.

Alertas.

Timeline.

Caja negra.

## Resultado esperado

Probar:

> **sensor + contexto + baseline + fusión = información más útil que sensores aislados.**

---

# 14. V2 · PLATAFORMA AVANZADA

Una vez validado V1 añadiremos:

* SpO₂;
* respiración;
* PPG bruto;
* EDA;
* ECG bajo demanda;
* presión arterial externa;
* báscula/BIA;
* calidad ambiental;
* CO₂;
* PM2.5;
* sueño avanzado;
* experimentos personales;
* reconocimiento de patrones;
* comparación con episodios anteriores;
* predicciones;
* modos personalizados.

Aquí aparece:

## Physiological Fingerprint

Una descripción dinámica del comportamiento habitual de cada organismo.

---

# 15. V3 · MOONSHOT

La visión avanzada.

Incorporaría potencialmente:

* parches de sudor;
* electrolitos;
* lactato;
* pH;
* cortisol;
* cetonas continuas;
* sensores de cama;
* smart ring;
* bandas ECG;
* integración domótica;
* analíticas periódicas;
* nuevos CGM;
* sensores bioquímicos futuros;
* federated learning;
* modelos poblacionales + personales.

El sistema podría construir un:

# PERSONAL PHYSIOLOGICAL DIGITAL MODEL

capaz de aprender relaciones complejas entre:

**metabolismo**

**corazón**

**sueño**

**temperatura**

**entorno**

**actividad**

**alimentación**

**recuperación**

---

# 16. Dos líneas de negocio separadas

## WELLNESS

Primera línea comercial.

Orientada a:

* autoconocimiento;
* tendencias;
* recuperación;
* hábitos;
* experimentos personales;
* contexto;
* detección de desviaciones personales.

No diagnostica.

---

## MEDICAL

Fase futura independiente.

Para:

* alertas médicas;
* monitorización clínica;
* soporte profesional;
* detecciones validadas.

Requerirá:

* validación;
* documentación;
* gestión de riesgos;
* regulación;
* posiblemente certificación como software sanitario.

No mezclaremos ambos productos inicialmente.

---

# 17. Principio regulatorio

V1 debe decir:

> "Tu frecuencia cardíaca está significativamente por encima de tu patrón habitual."

No:

> "Tienes una arritmia."

Puede decir:

> "Varias señales están cambiando simultáneamente."

No:

> "Estás enfermo."

Puede decir:

> "Las señales son compatibles con una carga térmica elevada."

No:

> "Tienes deshidratación."

Medición, inferencia y diagnóstico estarán claramente separados.

---

# 18. Arquitectura técnica V1

## Smartphone

Android.

## Reloj

Wear OS / Galaxy Watch inicialmente.

## Base local

Room / SQLite.

## Desarrollo

Kotlin.

## Comunicación

Bluetooth Low Energy.

## Procesamiento

Local / edge.

## Cloud

No obligatorio inicialmente.

## IA

No necesaria para V0.

---

# 19. Arquitectura de datos

Cada señal debe guardar como mínimo:

```text
timestamp

signal_type

value

unit

source

measurement_type

quality

context
```

Con:

```text
DIRECT
DERIVED
PREDICTED
USER_REPORTED
IMPORTED
```

Esto evita confundir mediciones reales con inferencias.

---

# 20. Estrategia de conexión al CGM

Orden de prioridad:

### A

Integración oficial/autorizada.

### B

Datos sincronizados o exportados para investigación y desarrollo.

### C

Investigación de conexión directa únicamente si es legal, segura y realmente necesaria.

El negocio nunca dependerá de alterar el firmware del Libre.

---

# 21. Privacidad

Principio:

# LOCAL FIRST

El móvil debe poder:

* recibir señales;
* analizar;
* detectar;
* alertar;
* guardar eventos;

sin necesidad de nube.

La nube podrá añadirse para:

* backup;
* histórico;
* sincronización;
* análisis pesado;
* modelos futuros.

---

# 22. Qué NO vamos a construir ahora

No construiremos todavía:

* hardware médico propio;
* sensor CGM propio;
* diagnóstico;
* portal sanitario;
* decenas de wearables;
* grandes modelos IA;
* infraestructura cloud compleja;
* red social;
* integración domótica completa;
* plataforma médica.

Primero validamos el núcleo.

---

# 23. MVP en 7 días

El primer MVP puede existir incluso sin sensores reales.

Construiremos un:

# SIMULADOR FISIOLÓGICO

Entradas:

* glucosa;
* FC;
* movimiento;
* temperatura cutánea;
* temperatura ambiente;
* humedad.

El simulador permitirá probar:

**baseline**

**cambio**

**persistencia**

**fusión**

**evento**

**alerta**

Esto nos permite trabajar inmediatamente.

---

# 24. Objetivo 30 días

Primer prototipo con datos reales.

Prioridad:

### Galaxy Watch → Android

Obtener:

* FC;
* movimiento;
* temperatura;
* IBI/HRV cuando sea viable.

Después:

### sensor ambiental BLE

Y paralelamente resolver:

### vía de adquisición de glucosa.

---

# 25. Objetivo 90 días

Primer prototipo completo:

```text
CGM
+
SMARTWATCH
+
AMBIENTE
        ↓
BODY DATA HUB
        ↓
PERSONAL BASELINE
        ↓
FUSION ENGINE
        ↓
8 EVENTOS
        ↓
RELOJ / MÓVIL
```

Con:

* dashboard;
* timeline;
* alertas;
* caja negra;
* feedback humano;
* historial.

---

# 26. Coste inicial estimado

Si desarrollamos nosotros el software:

### Hardware de prueba

Reloj compatible: aproximadamente **150–350 €**

Sensor ambiental BLE: aproximadamente **20–70 €**

Android: reutilizar teléfono existente.

FreeStyle Libre: dispositivo ya utilizado por el usuario.

### Software

Herramientas gratuitas o prácticamente gratuitas durante prototipo.

### Backend

0 € inicialmente.

### Coste MVP experimental

Aproximadamente:

# 200–450 €

más tiempo de desarrollo.

No necesitamos inversión significativa para validar el concepto.

---

# 27. Métrica de éxito del primer prototipo

No será:

> "¿Hemos creado IA?"

Será:

### 1

¿Recibimos las señales correctamente?

### 2

¿Las sincronizamos?

### 3

¿Identificamos contexto?

### 4

¿Creamos un baseline?

### 5

¿Detectamos un evento artificial/real?

### 6

¿El reloj recibe el aviso?

Si conseguimos eso:

# EL CONCEPTO TÉCNICO ESTÁ DEMOSTRADO.

---

# 28. Activo estratégico

El verdadero activo futuro no será el hardware.

Será:

# PERSONAL LONGITUDINAL PHYSIOLOGICAL MODEL

Cuanto más tiempo utiliza una persona el sistema:

más conoce su baseline;

más conoce sus respuestas;

más reconoce sus contextos;

más entiende sus anomalías;

más útil se vuelve.

Ese efecto acumulativo será una parte fundamental del valor del producto.

---

# 29. Producto resumido en una frase

> **Una plataforma que aprende cómo se comporta normalmente tu cuerpo y detecta cuándo varias señales empiezan a comportarse de forma diferente.**

---

# 30. Prioridad inmediata

A partir de este momento dejamos de añadir funcionalidades.

El orden de trabajo será:

**1. Nombre provisional del proyecto**

→ **2. Hardware exacto del prototipo**

→ **3. Viabilidad real de conexión Libre**

→ **4. Arquitectura Android/Wear OS**

→ **5. Simulador fisiológico**

→ **6. Primer agente cardiovascular**

→ **7. Primer agente metabólico**

→ **8. Fusion Engine**

→ **9. Primera alerta en reloj**

→ **10. Prueba con datos reales**

Ese es el camino para convertir la idea en producto.
