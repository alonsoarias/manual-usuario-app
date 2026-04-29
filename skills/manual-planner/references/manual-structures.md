# Plantillas de estructura de manual

Plantillas de partida para que el `manual-planner` proponga un plan inicial coherente con la profundidad declarada y el tipo de aplicación. **Son punto de partida, no camisas de fuerza**: el planner debe ajustar añadiendo o quitando secciones según el brief.

## 1. Plantillas por profundidad

### 1.1 Quickstart (5-15 páginas, 6-12 secciones)

Sólo el camino feliz de las 3-5 tareas más comunes.

| ID | Tipo | Título tentativo |
|----|------|------------------|
| S00 | portada | Portada |
| S01 | tabla-contenido-auto | Contenido |
| S02 | introduccion | Introducción |
| S03 | acceso | Cómo acceder |
| S04..S08 | tarea-paso-a-paso | Una sección por tarea principal |
| S09 | soporte | Soporte y contacto |

Recortes habituales: sin glosario, sin troubleshooting, sin apéndices, sin requisitos detallados.

### 1.2 Estándar (20-50 páginas, 12-25 secciones)

Cubre todas las tareas del bloque B2 con secciones de soporte completas.

| ID | Tipo | Título tentativo |
|----|------|------------------|
| S00 | portada | Portada |
| S01 | tabla-contenido-auto | Contenido |
| S02 | introduccion | Introducción |
| S03 | requisitos | Requisitos previos |
| S04 | acceso | Acceso al sistema |
| S05 | modulo | Visión general de la interfaz |
| S06..S{N-3} | tarea-paso-a-paso o modulo | Tareas y módulos |
| S{N-2} | troubleshooting | Solución de problemas |
| S{N-1} | glosario | Glosario |
| S{N} | soporte | Soporte y contacto |

### 1.3 Exhaustivo (60+ páginas, 25-50 secciones)

Cubre todas las tareas + casos límite + apéndices + glosario extendido.

| Bloque | Secciones |
|--------|-----------|
| Frontmatter | portada, contenido, introducción, convenciones, requisitos |
| Acceso y sesión | login, recuperación, cierre, gestión de perfil |
| Módulos principales | una sección de visión + sub-secciones por tarea |
| Casos avanzados | configuración avanzada, integraciones, exportaciones, importaciones |
| Operación | troubleshooting (general y por módulo), preguntas frecuentes |
| Backmatter | glosario, soporte, apéndices (atajos, formatos, plantillas) |

## 2. Variantes por tipo de aplicación

Las siguientes plantillas se aplican **encima** de la plantilla por profundidad: añaden o reemplazan secciones específicas del tipo de app declarado en el brief.

### 2.1 Aplicación móvil

Añadir o reemplazar:

- `requisitos` → especificar SO mínimos (iOS/Android), permisos solicitados, conectividad
- `acceso` → registro, biometría, recuperación, cierre por inactividad
- Sección "Modo sin conexión" (`modulo`) si la app la soporta
- Sección "Notificaciones" (`modulo`) describiendo tipos de push/local
- Sección "Deep links / esquemas de URL" (`apendice`) si aplica
- Capturas a viewport móvil (375x812 por defecto, 390x844 alternativo)

### 2.2 Aplicación con múltiples roles

Si el brief identifica más de un rol (p. ej. autor, revisor, editor; estudiante, docente, administrador):

- Crear un capítulo por rol, con su propia sección de "Acceso al rol" y tareas específicas.
- Añadir al frontmatter una matriz "Tareas × Rol" (apéndice tipo `apendice`).
- Las secciones compartidas entre roles van al frontmatter del manual; las específicas se agrupan por rol.

### 2.3 Plataforma editorial / CMS

Para Moodle, OJS, WordPress, Drupal, Joomla:

- Distinguir entre **plataforma** (instalación, configuración del sitio) y **uso final** (creación, edición, publicación).
- Si el brief documenta uso final únicamente, excluir todo lo administrativo.
- Sección "Roles y permisos" (`apendice` o `modulo`) con tabla rol × permiso.
- Sección "Plugins/módulos activados" (`apendice`) con lista de extensiones específicas de la instalación.

### 2.4 Aplicación de escritorio

Añadir o reemplazar:

- `requisitos` → especificar versiones de SO soportadas, requisitos de hardware, dependencias (runtime .NET, Java, etc.)
- Sección "Instalación" (`modulo`) con métodos por SO (instalador MSI/EXE, paquete .deb/.rpm, .dmg/.pkg)
- Sección "Atajos de teclado" (`apendice`)
- Sección "Actualización automática" (`modulo`) si la app la implementa
- Capturas a viewport 1366x768 por defecto

### 2.5 Aplicación web tipo dashboard / SaaS

- Sección "Visión general de la interfaz" (`modulo`) con captura anotada de la disposición principal.
- Sección "Personalización del entorno" (`modulo`) si hay temas, idiomas, preferencias.
- Sección "Permisos y compartición" (`modulo`) si hay objetos compartidos entre usuarios.
- Sección "Exportación de datos" (`modulo`) si aplica (CSV, PDF, API).

## 3. Reglas de combinación

Cuando una app pertenece a más de una categoría (p. ej. Moodle = web + CMS + multi-rol), aplicar las plantillas en este orden:

1. Plantilla por profundidad (base).
2. Plantilla por categoría primaria (web/móvil/escritorio/CMS).
3. Plantilla por características transversales (multi-rol, dashboard).

Eliminar secciones duplicadas. Si dos plantillas proponen una sección con el mismo título y tipo, conservar la más específica.

## 4. Heurística para decidir tipo `modulo` vs `tarea-paso-a-paso`

| Criterio | Usar `modulo` | Usar `tarea-paso-a-paso` |
|----------|---------------|--------------------------|
| Naturaleza | Visión panorámica de un área | Camino concreto para lograr un resultado |
| Inicio del lector | Llega aquí explorando | Llega aquí buscando hacer X |
| Capturas | 1-2, panorámicas | 3-5, una por paso clave |
| Verbos predominantes | Describir, mostrar, indicar | Hacer clic, escribir, seleccionar, confirmar |
| Tamaño típico | 2-4 páginas | 1-3 páginas |

Una misma área de la app puede tener una sección `modulo` (visión general) y varias secciones `tarea-paso-a-paso` que la complementan.

## 5. Catálogo de criterios de hecho reutilizables

Lista de criterios objetivos que el planner puede combinar al definir el "Criterio de hecho" de una sección. Cada uno es verificable por observación.

- Inicia con un párrafo de propósito de máximo 3 frases.
- Cada paso comienza con un verbo en imperativo.
- Cada paso describe una sola acción del usuario.
- Cada paso referencia una captura por su ID.
- Los nombres de elementos de UI (botones, campos, menús) se transcriben literalmente del inventario, en negrita o cursiva según convenciones.
- Los mensajes del sistema se citan textualmente entre comillas o monoespaciados.
- El criterio de éxito de la tarea se enuncia explícitamente al final de la sección.
- Incluye al menos una variante o caso de error si la tarea lo permite.
- No supera el límite superior de páginas estimadas en más de 0.5 páginas.
