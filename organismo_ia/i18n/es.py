"""Contenido en español de España (locale por defecto del organismo)."""

DATA = {
    "elements": {
        "earth": ["cuerpo", "dinero", "trabajo", "estabilidad", "salud", "hogar",
                   "seguridad", "material", "constancia", "raíz", "raiz", "sostén", "sosten"],
        "fire": ["pasión", "pasion", "acción", "accion", "voluntad", "energía", "energia",
                 "transformación", "transformacion", "ira", "impulso", "coraje", "deseo"],
        "water": ["emoción", "emocion", "intuición", "intuicion", "sueños", "suenos",
                  "sanación", "sanacion", "fluidez", "sentir", "duelo", "vínculo", "vinculo"],
        "air": ["mente", "ideas", "comunicación", "comunicacion", "claridad", "estrategia",
                "pensar", "análisis", "analisis", "palabra", "plan"],
        "ether": ["espíritu", "espiritu", "propósito", "proposito", "conexión", "conexion",
                  "sincronía", "sincronia", "alma", "trascender", "unidad", "silencio"],
    },
    "default_element": "air",
    "element_names": {"earth": "Tierra", "fire": "Fuego", "water": "Agua", "air": "Aire", "ether": "Éter"},
    "classification_names": {"attractor": "atractor", "detractor": "detractor", "neutral": "neutro"},
    "attractor_keywords": [
        "expansión", "expansion", "gratitud", "abundancia", "amor", "crecimiento",
        "oportunidad", "confianza", "claridad", "alegría", "alegria", "sí puedo",
        "si puedo", "gracias", "logro", "avance", "apertura",
    ],
    "detractor_keywords": [
        "miedo", "duda", "escasez", "bloqueo", "no puedo", "estrés", "estres",
        "caos", "ansiedad", "culpa", "vergüenza", "verguenza", "no sirvo",
        "fracaso", "rechazo", "abandono", "no hay",
    ],
    "agents": {
        "Solkin": {
            "detractor": ("Baja al cuerpo: tres respiraciones lentas, apoya los pies en el "
                           "suelo y realiza una activación breve (movilidad de cadera y "
                           "hombros) antes de continuar."),
            "default": ("Sostén la energía con una activación corporal breve: postura "
                        "erguida, respiración diafragmática y un paseo de 5-10 minutos "
                        "para integrar."),
        },
        "Vitalion": {
            "detractor_tmpl": "Ritmo bajo — puerta {gate}: frena el impulso, no actúes desde la urgencia.",
            "default_tmpl": "Ritmo alto — puerta {gate}: es el momento de actuar, el impulso está a favor.",
        },
        "Almir": {
            "detractor": "Fórmula sugerida: infusión calmante (manzanilla/lavanda) y exposición solar breve al amanecer.",
            "default": "Fórmula sugerida: agua solarizada y una planta de compañía para sostener el estado actual.",
        },
        "Nodar": {
            "default": ("Es traducible a arquitectura digital: este contenido podría "
                        "materializarse como un nodo/escena dentro del ecosistema "
                        "(Metaverso Nodal), coherente con el elemento activo."),
        },
        "Helion": {
            "detractor": "Señal de escasez detectada: revisa el flujo antes de comprometer nuevos nodos económicos.",
            "default": "Flujo favorable: es un buen momento para expandir un nodo económico existente.",
        },
        "Paradion": {
            "default": "Este contenido tiene potencial narrativo: podría convertirse en una experiencia o pieza compartible.",
        },
        "Synar": {
            "tmpl": ("Elemento activo: {element} · Puerta Tesla: {gate} · Lectura: {classification}. "
                     "Integrando las voces anteriores en una sola dirección."),
        },
        "Arkhon": {
            "ok": "Integridad verificada. Flujo protegido.",
            "empty_error": "Entrada vacía: el organismo no puede procesar el silencio absoluto como texto.",
        },
        "Jakhar": {
            "flagged_tmpl": "Patrón de interferencia detectado y neutralizado ({n} marcador(es)).",
            "clean": "Sin ruido ni interferencia detectada.",
        },
    },
    "ui": {
        "portal": {
            "title": "Portal",
            "description": "Punto de entrada del organismo: texto, voz, cámara o archivos.",
            "action_label": "Invocar al organismo",
        },
        "ritual_mode": {
            "title": "Rituales",
            "description": "Protocolos corporales y rituales guiados almacenados en la memoria interna.",
            "action_label": "Iniciar ritual",
        },
        "lab_mode": {
            "title": "Laboratorio",
            "description": "Fórmulas (Almir) y arquitecturas (Nodar/Helion) en construcción.",
            "action_label": "Guardar fórmula",
        },
        "metaverso_mode": {
            "title": "Metaverso Nodal",
            "description": "Proyectos y nodos digitales (Nodar/Helion) desde la memoria interna.",
            "action_label": "Abrir nodo",
        },
    },
    "llm_prompt": (
        "Eres Synar, el agente de síntesis de un organismo de IA simbólico. "
        "Elemento activo: {element}. Puerta Tesla: {gate}. Lectura: {classification}.\n"
        "Estas son las voces de los agentes internos que ya han intervenido:\n{fragments}\n\n"
        "Mensaje original del usuario: {text}\n\n"
        "Integra esas voces en una única respuesta coherente, breve y en español, dirigida al usuario."
    ),
    "errors": {
        "unknown_ui_mode": "Modo de UI desconocido: '{mode}'. Válidos: {valid}",
    },
}
