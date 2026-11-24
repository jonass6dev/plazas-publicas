# Plan: Agentes de plazas públicas (Comunitat Valenciana)

## 1. Objetivo

Construir dos agentes dentro de este proyecto:

1. **Agente Recolector** – vigila las convocatorias de empleo público en la Comunitat Valenciana, extrae los datos y los guarda de forma estructurada.
2. **Agente Web** – construye y mantiene una web sencilla que muestra y esquematiza esa información.

**¿Es posible?** Sí. Las dos partes son viables con Claude Code. Un matiz importante: un agente no "está pendiente" de forma permanente por sí solo. Lo que se hace es **ejecutarlo de forma periódica** (p. ej. cada día) con una tarea programada, y que cada ejecución compare lo nuevo con lo ya guardado.

## 2. Arquitectura

```
 Fuentes oficiales ──► Agente Recolector ──► data/plazas.json ──► Agente Web ──► web/ (sitio estático)
 (DOGV, BOE, BOP,        (descarga, extrae,    (única fuente        (genera y        (HTML + JS,
  ayuntamientos...)       normaliza, deduplica)  de verdad)          mantiene la web)  publicable)
```

El **contrato entre agentes es el fichero `data/plazas.json`** (más un esquema JSON). Así los agentes son independientes: el recolector no sabe nada de la web y la web solo lee el JSON.

## 3. Estructura de carpetas propuesta

```
agente-plazas-publicas/
├── docs/
│   └── plan.md                  ← este documento
├── .claude/
│   └── agents/
│       ├── recolector.md        ← definición del subagente 1
│       └── web.md               ← definición del subagente 2
├── scrapers/                    ← un módulo por fuente (código determinista)
│   ├── dogv.py
│   ├── boe.py
│   ├── bop_valencia.py
│   └── ...
├── data/
│   ├── plazas.json              ← datos normalizados (salida del recolector)
│   ├── schema.json              ← esquema de validación
│   └── raw/                     ← descargas originales (para auditar)
├── web/                         ← sitio estático (salida del agente web)
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── README.md
```

## 4. Agente 1 – Recolector

### 4.1 Fuentes (a verificar en la fase 0)

| Prioridad | Fuente | Qué aporta | Acceso probable |
|---|---|---|---|
| Alta | **DOGV** (Diari Oficial de la Generalitat Valenciana) | Convocatorias de la Generalitat, universidades, entes autonómicos | Web con búsqueda / datos abiertos |
| Alta | **BOE** | Convocatorias estatales con destino en la C. Valenciana | API de datos abiertos (sumarios en XML/JSON) |
| Alta | **BOP** de Valencia, Alicante y Castellón | Ayuntamientos y diputaciones | Web / RSS |
| Media | Portal de empleo público de la GVA | Ofertas de empleo público, oposiciones, bolsas | Web |
| Media | Universidades públicas (UV, UPV, UA, UMH, UJI) | PAS y PDI | Web de cada una |
| Baja | Sedes electrónicas de ayuntamientos grandes (Valencia, Alicante, Elche, Castellón) | Convocatorias propias | Web, formato variable |

> Antes de programar cada scraper hay que comprobar los **términos de uso y el `robots.txt`** de la fuente y preferir siempre APIs/datos abiertos o RSS frente a rascar HTML.

### 4.2 Responsabilidades

- Descargar las publicaciones nuevas desde la última ejecución.
- Filtrar las que sean de empleo público (oposiciones, concursos, bolsas, procesos de estabilización…).
- **Extraer campos estructurados** (aquí es donde Claude aporta valor: leer textos administrativos poco uniformes y rellenar el esquema).
- Normalizar, deduplicar y guardar en `data/plazas.json`.
- Marcar plazas cuyo plazo ya ha vencido.
- Dejar un registro de cada ejecución (qué fuentes, cuántas plazas nuevas, errores).

### 4.3 Esquema de datos de una plaza

```json
{
  "id": "dogv-2026-12345",
  "titulo": "Técnico/a de Administración General",
  "organismo": "Ayuntamiento de Alicante",
  "ambito": "local",                  
  "provincia": "Alicante",
  "tipo_proceso": "oposición",        
  "grupo": "A1",
  "num_plazas": 3,
  "titulacion": "Grado en Derecho",
  "fecha_publicacion": "2026-11-20",
  "fecha_limite": "2026-12-10",
  "estado": "abierto",                
  "url_oficial": "https://...",
  "fuente": "DOGV",
  "extraido_el": "2026-11-24T08:00:00Z"
}
```

### 4.4 Diseño recomendado (híbrido)

- **Código determinista** (`scrapers/`) para descargar y detectar novedades: es barato, rápido y reproducible.
- **Claude (subagente)** solo para lo que requiere comprensión de texto: clasificar, extraer campos y resolver casos ambiguos.
- **Validación** del resultado contra `schema.json`; si falla, no se escribe en `plazas.json`.
- Cada plaza guarda siempre el **enlace oficial**: la web es un índice, no una fuente legal.

## 5. Agente 2 – Web

### 5.1 Requisitos

- Sitio **estático y sencillo** (HTML + JS + CSS, sin backend), que lee `data/plazas.json`.
- Vista principal: tabla/tarjetas de plazas ordenables.
- **Filtros**: provincia, organismo, tipo de proceso, grupo, estado, plazo.
- **Buscador** por texto.
- Resaltar las plazas **que cierran pronto** y las **nuevas** de la última semana.
- Resumen superior: nº de plazas abiertas, nuevas esta semana, próximas a vencer.
- Diseño responsive (móvil primero) y accesible.
- Enlace a la fuente oficial en cada plaza.

### 5.2 Responsabilidades del agente

- Crear la web la primera vez y mantenerla cuando cambie el esquema de datos.
- Probarla en el navegador (carga con datos reales, filtros funcionan, móvil).
- No modificar `data/` (solo lectura).

### 5.3 Publicación (a decidir)

Opciones gratuitas: GitHub Pages, Netlify o Cloudflare Pages. Se empieza en local y se publica cuando el MVP funcione.

## 6. Cómo se crean los agentes en Claude Code

- Cada agente es un **subagente** definido en `.claude/agents/<nombre>.md` con su descripción, herramientas permitidas y su prompt de sistema.
  - `recolector`: acceso a Bash, lectura/escritura en `scrapers/` y `data/`, búsqueda web.
  - `web`: lectura de `data/`, escritura solo en `web/`, acceso al navegador para verificar.
- **Ejecución periódica**: una tarea programada (diaria, p. ej. a las 08:00) que lanza al recolector y, si hay cambios, al agente web. Opciones: tareas programadas de Claude Code, o el Programador de tareas de Windows / GitHub Actions ejecutando los scrapers.

## 7. Fases

| Fase | Contenido | Resultado |
|---|---|---|
| **0. Descubrimiento** | Revisar cada fuente: formato, API, RSS, robots.txt, frecuencia de publicación. Elegir 2–3 fuentes para el MVP. | Tabla de fuentes validada |
| **1. Modelo de datos** | Cerrar `schema.json` y el formato de `plazas.json`. | Contrato entre agentes |
| **2. Recolector MVP** | Un scraper (DOGV o BOE) + extracción con Claude + validación. | `plazas.json` con datos reales |
| **3. Web MVP** | Lista + filtros + buscador sobre `plazas.json`. | Web en local |
| **4. Más fuentes** | Añadir BOP, universidades y ayuntamientos uno a uno. | Cobertura ampliada |
| **5. Automatización** | Tarea diaria, registro de ejecuciones, aviso si una fuente falla. | Funcionamiento autónomo |
| **6. Publicación y extras** | Hosting, y opcionalmente alertas por email o RSS propio. | Web pública |

## 8. Riesgos y decisiones

- **Fuentes heterogéneas**: cada ayuntamiento publica distinto; se cubre por fases y priorizando por volumen.
- **Cambios en las webs de origen** rompen los scrapers: de ahí el registro de errores y la validación.
- **Errores de extracción del LLM** (fechas, nº de plazas): validar con el esquema, guardar el texto original en `data/raw/` y enlazar siempre al documento oficial.
- **Legalidad y buenas prácticas**: respetar `robots.txt`, límites de peticiones y condiciones de reutilización. Las publicaciones en boletines oficiales son, en general, información pública reutilizable, pero se debe verificar por fuente.
- **Aviso en la web**: indicar que la información es orientativa y que prevalece la publicación oficial.

## 9. Preguntas abiertas

1. ¿Qué ámbito interesa? ¿Solo Generalitat y ayuntamientos grandes, o todos los municipios?
2. ¿Solo oposiciones o también bolsas de trabajo/interinos y concursos?
3. ¿Web solo para uso personal (local) o pública?
4. ¿Lenguaje preferido para los scrapers (Python recomendado) y para la web (HTML/JS plano, o un framework)?
5. ¿Quieres alertas (email, Telegram) además de la web?

## 10. Siguiente paso

Aprobar este plan y responder a las preguntas de la sección 9. Después se empieza por la **Fase 0** (revisar fuentes) y la **Fase 1** (esquema de datos).
