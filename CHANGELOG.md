# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versionado semántico.

## [2.0.0] - 2026-10-07

### Cambios que rompen compatibilidad
- Esquema de `MANIFIESTO.md`: nuevas columnas `Pantalla` y `Enmascarado`; un manifiesto sin ellas bloquea el check C13. El inventario gana la columna `pii` y el plan separa `enmascarar` de `anotación` (`tachado-datos` desaparece; migración en `skills/manual-planner/SKILL.md:107`): un plan o inventario v1 bloquea C13.
- Enmascarado: `pii: sí` del inventario prevalece sobre `enmascarar: no` del plan; solo una `excepción: <motivo>` aprobada por el PO lo evita.
- El script de compilación de DOCX se unifica en `compile_pandoc.sh --to docx|html|gfm`; el nombre anterior desaparece.
- `concatenate.py` (rc 2) rechaza: imágenes remotas (`http(s):`, `//`; solo se admite `data:`), imágenes fuera del manual o con otros esquemas, definiciones de imagen por referencia con ruta relativa, enlaces con esquema fuera de `http`, `https`, `mailto`, `tel`, relativo o ancla, metadatos fuera de `ALLOWED_METADATA` e `idioma` fuera de es/en/pt. El PDF rechaza los enlaces simbólicos con rc 6; las demás salidas los omiten con aviso.
- C12 es bloqueante cuando el brief pide `formato.html` o `formato.markdown`.
- El PDF por LaTeX desactiva `raw_tex`, `raw_attribute` y las matemáticas `$...$`.
- Si Typst está instalado y falla, `compile_pdf.sh` termina con rc 5 sin caer a LaTeX.

### Añadido
- Bucle de corrección por rondas con re-verificación acotada al delta y `estado.md` por manual.
- Salidas HTML autocontenido y Markdown/GFM además de DOCX y PDF.
- Idiomas es, en y pt (`--idioma`), una carpeta de manual por idioma; guía de redacción por idioma; check C12.
- Enmascarado de datos personales antes de capturar (fuente única `pii-masking.md`) y check C13.
- Referencias del analizador para SaaS/API y flujos de autenticación (2FA sin capturar códigos).
- Suite de tests de los scripts (`tests/`) y 5 evals (`evals/`).

### Seguridad
- Compilación endurecida contra inyección vía Markdown no confiable (LaTeX, XSS por atributos y esquemas `javascript:`, enlaces simbólicos, validación de imágenes sobre el AST de pandoc).

## [1.0.0]
- Versión inicial: workflow de 7 fases, DOCX/PDF, captura vía MCP, verificador C1-C11.
