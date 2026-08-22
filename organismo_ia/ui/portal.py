"""
ui/portal — capa 1/4 del spec: contrato JSON del modo de entrada
principal. Este backend no renderiza UI (eso es Flutter/React Native,
sección 4.1); expone la estructura que un frontend usa para dibujar la
pantalla, consistente con cómo backend/main.py ya sirve un frontend
estático propio en /agent.
"""


def describe() -> dict:
    return {
        "mode": "portal",
        "title": "Portal",
        "description": "Punto de entrada del organismo: texto, voz, cámara o archivos.",
        "inputs": ["text", "voice", "camera", "file"],
        "actions": [{"id": "invoke", "label": "Invocar al organismo"}],
    }
