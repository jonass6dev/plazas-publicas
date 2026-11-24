# Plazas públicas · Comunitat Valenciana

Web sencilla con las convocatorias de empleo público de la Comunitat Valenciana publicadas en el BOE.
Se actualiza sola cada día con GitHub Actions.

- `scrapers/boe.py`: lee la API de datos abiertos del BOE y genera `data/plazas.json` (solo biblioteca estándar de Python 3).
- `data/schema.json`: esquema de los datos.
- `web/`: la web estática (HTML, CSS, JS).
- `.github/workflows/actualizar.yml`: tarea diaria que ejecuta el scraper y publica en GitHub Pages.
- `docs/`: plan y revisión de fuentes.

## Uso en local

```
python scrapers/boe.py --dias 30
python -m http.server 8765
```

Abre http://localhost:8765/web/

## Aviso

Información orientativa extraída automáticamente. Las fechas límite son estimadas (no se descuentan festivos).
Comprueba siempre el plazo y las bases en la publicación oficial. Fuente: BOE (datos abiertos).
