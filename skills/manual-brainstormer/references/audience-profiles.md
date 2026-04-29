# Calibración de profundidad y tono según perfil de audiencia

Este documento ofrece tablas de referencia para que el `manual-brainstormer` y los redactores de la fase 5 ajusten densidad, longitud y vocabulario al perfil identificado en B1.

## 1. Calibración por nivel TIC

El nivel TIC declarado en el brief determina cuánto contexto se asume y cuántas capturas se incluyen.

| Variable | Nivel TIC bajo | Nivel TIC medio | Nivel TIC alto |
|----------|----------------|-----------------|----------------|
| Capturas por sección de tarea | 3-5 | 1-3 | 0-1 (referencias en texto) |
| Anotaciones sobre captura | Obligatorias (números, flechas) | Recomendadas | Opcionales |
| Tamaño tipográfico sugerido | 12 pt | 11 pt | 10-11 pt |
| Glosario | Extendido (40+ términos) | Estándar (15-30) | Mínimo o ausente |
| Longitud media de párrafo | ≤ 35 palabras | ≤ 60 palabras | ≤ 90 palabras |
| Frases por párrafo | 1-2 | 2-3 | 3-5 |
| Verbo por paso | 1 | 1-2 | varios |
| Tono | Tutoreo cercano y directo | Profesional neutro | Técnico preciso |
| Uso de jerga | Evitar; explicar siempre | Permitida con primera mención explicada | Permitida sin glosa |
| Profundidad por defecto | Quickstart o estándar | Estándar | Estándar o exhaustivo |

## 2. Tareas a la medida del nivel TIC

| Nivel TIC | Cómo se describe una tarea |
|-----------|----------------------------|
| Bajo | Cada paso comienza con un verbo en imperativo directo. Cada paso referencia una captura. Se nombra el botón exacto entre comillas o en negrita. Se evitan condicionales en el camino feliz. |
| Medio | Pasos numerados. Captura cada 2-3 pasos. Variantes ("si X, entonces Y") permitidas pero relegadas al final de la sección o a un recuadro "Nota". |
| Alto | Pasos resumidos. Capturas sólo cuando aportan información que el texto no transmite. Variantes integradas en flujo continuo. |

## 3. Perfiles típicos por sector (genéricos)

Los perfiles siguientes son arquetipos genéricos que el brainstormer puede usar como punto de partida cuando el usuario dude sobre cómo describir su audiencia. **No** sustituyen la respuesta del cliente: son ejemplos.

### 3.1 Sector educativo

| Sub-perfil | Nivel TIC | Características |
|------------|-----------|-----------------|
| Estudiante universitario | medio-alto | Familiaridad con plataformas LMS, expectativa de UX moderna, tolerancia a textos largos baja |
| Estudiante secundario | medio | Uso intensivo de móvil, baja tolerancia a flujos largos |
| Docente nativo digital | medio-alto | Necesita hojas de ruta para escenarios pedagógicos, no para clics individuales |
| Docente con baja exposición digital | bajo | Requiere capturas grandes, anotaciones explícitas, glosario, lenguaje sin anglicismos |

### 3.2 Sector corporativo

| Sub-perfil | Nivel TIC | Características |
|------------|-----------|-----------------|
| Personal administrativo | medio | Uso 8h/día, valora atajos y eficiencia; tolerancia media a la lectura |
| Personal operativo en planta | bajo-medio | Dispone de poco tiempo, suele consultar el manual en pantalla pequeña o impreso |
| Mando intermedio | medio-alto | Lee secciones específicas, salta el resto; necesita TOC útil |
| Personal directivo | medio | Lee resúmenes y tableros; rara vez sigue pasos detallados |

### 3.3 Sector público

| Sub-perfil | Nivel TIC | Características |
|------------|-----------|-----------------|
| Funcionario administrativo | bajo-medio | Audiencia heterogénea por edad y formación; tono institucional |
| Funcionario técnico | medio-alto | Tolera vocabulario especializado, valora precisión normativa |
| Ciudadano usuario de trámites | bajo | Acceso esporádico, expectativa de rapidez, tolerancia cero a la jerga |

### 3.4 Sector salud

| Sub-perfil | Nivel TIC | Características |
|------------|-----------|-----------------|
| Personal asistencial (médicos, enfermería) | medio | Tiempo escaso por consulta, valora flujos cortos, terminología clínica permitida |
| Personal administrativo de salud | bajo-medio | Manejo de agendas y trámites; tono procedimental |
| Paciente usuario de portal | variable | Calibrar caso a caso; en general tono claro y empático |

### 3.5 Investigación y publicaciones

| Sub-perfil | Nivel TIC | Características |
|------------|-----------|-----------------|
| Autor académico | medio-alto | Conoce el campo, no la plataforma; manuales por rol (autor, revisor, editor) |
| Revisor par | medio-alto | Lectura selectiva; necesita encontrar rápido el flujo de revisión |
| Editor de revista | alto | Valora vista panorámica del flujo editorial completo |

## 4. Bandera roja: cuándo repreguntar B1

El brainstormer debe insistir en B1 si el usuario responde con expresiones como:

- "todos los usuarios", "todo el mundo", "cualquiera"
- "el público general", "el ciudadano"
- "los empleados" (sin más detalle)
- un solo adjetivo ("usuarios novatos")

La pregunta de seguimiento sugerida: *"¿Puede describirme una persona concreta que vaya a usar este manual? Edad aproximada, formación, qué dispositivo usa, en qué momento del día consulta el manual."*

## 5. Cálculo de páginas objetivo

A partir del nivel TIC y la cantidad de tareas de B2, el brainstormer puede sugerir un valor coherente para `paginas_objetivo`:

```
paginas_objetivo ≈ paginas_base + (tareas × paginas_por_tarea)

paginas_base:           portada + TOC + intro + acceso + soporte + glosario ≈ 10
paginas_por_tarea:      bajo TIC = 3 ; medio = 2 ; alto = 1
```

Si el resultado supera el rango declarado en `profundidad`, ofrecer al usuario:
- subir la profundidad
- recortar tareas
- reducir capturas por tarea (consultando los rangos de la sección 1)
