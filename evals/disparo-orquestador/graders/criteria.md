---
type: llm
weight: 1
---

Pasa si el agente reconoce la petición como creación de un manual de usuario y activa o aplica el flujo del plugin manual-usuario-app (invoca la skill manual-orchestrator o manual-brainstormer, o describe explícitamente el workflow por fases de ese plugin). Falla si responde con consejos genéricos de documentación sin usar el flujo del plugin, o si empieza a redactar el manual completo sin más.
