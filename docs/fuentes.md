# Fase 0: revisión de fuentes (24/11/2026)

Resultado de comprobar cada fuente con peticiones reales y su `robots.txt`.

## Resumen

| Fuente | Acceso | Estado | Decisión |
|---|---|---|---|
| **BOE** (API de datos abiertos) | JSON/XML oficial: `https://www.boe.es/datosabiertos/api/boe/sumario/AAAAMMDD` con `Accept: application/json` | ✅ Funciona (probado, HTTP 200) | **Fuente 1 del MVP** |
| **DOGV** | Sin API ni RSS localizados. `/es/rss` devuelve una página HTML, no un feed. Su `robots.txt` bloquea `/datos/` (los PDF) a todos los robots | ⚠️ Restringido | No rascar PDF. Buscar acceso por datos abiertos o el listado HTML permitido (por confirmar) |
| **GVA** (`gva.es`) | `robots.txt` bloquea explícitamente a bots de IA, incluidos `ClaudeBot` y `Claude-User` | ⛔ Bloqueado para este uso | No acceder automáticamente. Valorar contactar con la GVA o usar solo el DOGV |
| **Datos abiertos GVA** (`dadesobertes.gva.es`) | API CKAN real (`/api/3/action/package_search`), 29 conjuntos con "empleo público" | ✅ Funciona | Revisar si alguno contiene convocatorias (los vistos son de otro tema: expedientes de regulación) |
| **BOP Valencia** (`bop.dival.es`) | Web JSF/PrimeFaces con `<meta robots="nofollow">`, sin feed localizado, sin `robots.txt` | ⚠️ Difícil | Fase posterior; pedir feed o buscar su alternativa |
| **BOP Castellón** (`bop.dipcas.es`) | Responde, sin `robots.txt`, feed no localizado | ❓ Sin evaluar | Fase posterior |
| **BOP Alicante** | `bop.diputacionalicante.es` no responde; el servicio cuelga de `sede.diputacionalicante.es` | ❓ Sin evaluar | Fase posterior |
| Universidades, ayuntamientos | No revisados | ❓ | Fase posterior, uno a uno |

## Conclusiones

1. **La única fuente limpia y oficial hoy es el BOE.** Su sección "II.B Oposiciones y concursos" incluye personal funcionario, laboral y estatutario de servicios de salud. Se puede filtrar por texto "Comunitat Valenciana", "Valencia", "Alicante", "Castellón".
2. **El BOE no cubre lo más relevante de la región**: la Generalitat, las diputaciones y los ayuntamientos publican en DOGV y BOP. Esa información es la que más interesa y la que tiene más trabas de acceso.
3. **Dos fuentes se oponen explícitamente al acceso automatizado** (`/datos/` del DOGV y los bots de IA en `gva.es`). Se respetan: no se programan scrapers contra esas rutas.

## Dato útil

La OPE 2026 de la Generalitat prevé 2.671 plazas y la de 2027 prevé 1.116 (según los resultados de búsqueda; sin verificar en la fuente primaria).

## Decisiones propuestas

- **MVP**: BOE (API) + revisión de conjuntos de `dadesobertes.gva.es`.
- **DOGV**: investigar si hay una vía permitida (listados HTML no bloqueados o datos abiertos). Si no, pedir autorización o un feed a la GVA.
- **BOP y ayuntamientos**: por fases, tras ver cuáles ofrecen RSS o datos abiertos.
- **Tu decisión pendiente**: si el DOGV no ofrece vía permitida, ¿se acepta una cobertura inicial parcial (BOE + datos abiertos) o se prefiere contactar con la GVA antes de seguir?

## Siguiente paso

Fase 1: cerrar `data/schema.json` y construir el primer scraper del BOE.
