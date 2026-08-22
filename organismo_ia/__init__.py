"""
Organismo IA Local — implementación ejecutable del documento técnico
(Organismo IA Local · Arquitectura Ejecutable, v1.0, 22/08/2026).

Este paquete implementa, en Python puro (sin dependencias nuevas), las
capas del spec que pueden correr en un backend cloud/servidor:

  - capa 5 (IA local / Cerebro-Baúl)  -> core/
  - capa 7 (agentes internos)         -> agents/
  - capa 6 (memoria)                  -> memory/
  - capa 4 (cuerpo / módulos)         -> modules/
  - capa 1/4 (UI)                     -> ui/ (contratos JSON para un frontend)
  - capa 8 (seguridad, Arkhon/Jakhar) -> agents/arkhon.py, agents/jakhar.py

Lo que el spec pide que corra *en el dispositivo* (STT/TTS, cámara,
sensores, un LLM comprimido on-device) no puede ejecutarse en este
entorno de servidor: esos módulos quedan como interfaces documentadas
(ver modules/voice.py, modules/vision.py, modules/movement.py) listas
para que un cliente móvil (Flutter/Kotlin/Swift, sección 4.1 del spec)
las implemente. Ver README.md de este paquete para el detalle completo.
"""

from .core.synthesis_engine import run, OrganismoResult  # noqa: F401 (API pública del paquete)

__all__ = ["run", "OrganismoResult"]
