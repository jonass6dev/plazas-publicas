"""Scraper del BOE (API oficial de datos abiertos) -> data/plazas.json.

Solo usa la biblioteca estándar. Uso:
    python scrapers/boe.py            # últimos 30 días
    python scrapers/boe.py --dias 7
Es incremental: conserva lo ya guardado y añade lo nuevo.
"""
import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "plazas.json"
API = "https://www.boe.es/datosabiertos/api/boe/sumario/{}"
UA = "agente-plazas-publicas/0.1 (proyecto personal; consulta diaria)"
PAUSA = 1.0  # segundos entre peticiones

# Qué relaciona un anuncio con la Comunitat Valenciana
CV_RE = re.compile(
    r"comunitat valenciana|comunidad valenciana|generalitat valenciana|generalitat"
    r"|universitat de val[eè]ncia|universidad de valencia|polit[eè]cnica de val[eè]ncia"
    r"|universidad de alicante|universitat d.alacant|jaume i|miguel hern[aá]ndez"
    r"|\bvalencia\b|\bval[eè]ncia\b|\balicante\b|\balacant\b|castell[oó]n|castell[oó] de la plana"
    r"|elche|elx\b|torrevieja|gandia|benidorm|sagunto|orihuela|alcoy|alcoi",
    re.I,
)
PROV = {"Valencia": r"valencia|val[eè]ncia|sagunto|gandia", "Alicante": r"alicante|alacant|elche|elx|torrevieja|benidorm|orihuela|alcoy|alcoi",
        "Castellón": r"castell[oó]n|castell[oó] de la plana"}


def get(url, accept=None):
    h = {"User-Agent": UA}
    if accept:
        h["Accept"] = accept
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def listar(d):
    """Items de la sección 2B (oposiciones y concursos) de un día."""
    try:
        data = json.loads(get(API.format(d.strftime("%Y%m%d")), "application/json"))
    except urllib.error.HTTPError as e:
        if e.code == 404:  # domingo / sin boletín
            return
        raise
    for diario in _lista(data["data"]["sumario"]["diario"]):
        for sec in _lista(diario.get("seccion")):
            if sec["codigo"] != "2B":
                continue
            for dep in _lista(sec.get("departamento")):
                for epi in _lista(dep.get("epigrafe")):
                    for it in _lista(epi.get("item")):
                        yield dep["nombre"], epi.get("nombre", ""), it


def _lista(x):
    return [] if x is None else x if isinstance(x, list) else [x]


def texto_html(url):
    t = get(url)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t))


NUM = {"cinco": 5, "diez": 10, "quince": 15, "veinte": 20, "treinta": 30, "veinticinco": 25, "veintiun": 21, "veintiuno": 21, "sesenta": 60, "dos": 2, "tres": 3}


def extraer_plazo(txt):
    """(días, 'habiles'|'naturales') a partir del texto de la convocatoria."""
    m = re.search(r"plazo[^.]{0,120}?(?:ser[aá]|es|de)\s+(?:de\s+)?(\w+)(?:\s*\((\d+)\))?\s+d[ií]as\s+(h[aá]biles|naturales)", txt, re.I)
    if not m:
        return None, None
    n = int(m.group(2)) if m.group(2) else int(m.group(1)) if m.group(1).isdigit() else NUM.get(m.group(1).lower())
    return n, ("habiles" if m.group(3).lower().startswith("h") else "naturales")


def sumar_dias(desde, n, tipo):
    if tipo == "naturales":
        return desde + timedelta(days=n)
    return sumar_habiles(desde, n)


def sumar_habiles(desde, n):
    d, c = desde, 0
    while c < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            c += 1
    return d


def clasificar_proceso(titulo):
    t = titulo.lower()
    if "bolsa" in t:
        return "bolsa"
    if "concurso-oposici" in t or "concurso oposici" in t:
        return "concurso-oposicion"
    if "concurso" in t:
        return "concurso"
    if "proceso selectivo" in t or "oposici" in t or "ingreso" in t:
        return "oposicion"
    return "otro"


def ambito(dep):
    d = dep.lower()
    if "universidad" in d:
        return "universidad"
    if "comunitat valenciana" in d or "comunidad valenciana" in d:
        return "autonomico"
    if "administraci" in d and "local" in d:
        return "local"
    return "estatal"


def procesar(d, hoy):
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for dep, epi, it in listar(d):
        titulo = it["titulo"]
        if not re.search(r"por la que se (convoca|aprueba la convocatoria)|convocatoria|se convocan", titulo, re.I):
            continue  # descartamos nombramientos, listas, resultados...
        m = CV_RE.search(f"{dep} {epi} {titulo}")
        if not m:
            continue
        time.sleep(PAUSA)
        try:
            cuerpo = texto_html(it["url_html"])
        except Exception as e:  # noqa: BLE001
            print(f"  aviso: no se pudo leer {it['identificador']}: {e}")
            cuerpo = ""
        dias, tipo_dias = extraer_plazo(cuerpo)
        pub = d
        limite = sumar_dias(pub, dias, tipo_dias) if dias else None
        np_ = re.search(r"(\d+)\s+plazas?", titulo + " " + cuerpo[:3000], re.I)
        prov = next((p for p, rx in PROV.items() if re.search(rx, f"{dep} {epi} {titulo}", re.I)), None)
        yield {
            "id": "boe-" + it["identificador"],
            "titulo": titulo,
            "organismo": dep.title() if dep.isupper() else dep,
            "ambito": ambito(dep),
            "provincia": prov,
            "tipo_proceso": clasificar_proceso(titulo),
            "num_plazas": int(np_.group(1)) if np_ else None,
            "plazo_dias": dias,
            "tipo_dias": tipo_dias,
            "fecha_publicacion": pub.isoformat(),
            "fecha_limite": limite.isoformat() if limite else None,
            "fecha_limite_estimada": bool(limite),
            "estado": ("abierto" if limite >= hoy else "cerrado") if limite else "desconocido",
            "url_oficial": it["url_html"],
            "fuente": "BOE",
            "coincidencia_cv": m.group(0),
            "extraido_el": ahora,
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=30)
    a = ap.parse_args()
    hoy = date.today()
    previo = {}
    if OUT.exists():
        previo = {p["id"]: p for p in json.loads(OUT.read_text(encoding="utf-8"))["plazas"]}
    nuevas = 0
    for i in range(a.dias, -1, -1):
        d = hoy - timedelta(days=i)
        if d.weekday() == 6:
            continue
        for p in procesar(d, hoy):
            if p["id"] not in previo:
                nuevas += 1
            previo[p["id"]] = p
        time.sleep(PAUSA)
    # recalcular estado de lo ya guardado
    for p in previo.values():
        if p["fecha_limite"]:
            p["estado"] = "abierto" if date.fromisoformat(p["fecha_limite"]) >= hoy else "cerrado"
    plazas = sorted(previo.values(), key=lambda p: p["fecha_publicacion"], reverse=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"actualizado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "plazas": plazas}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Hecho: {len(plazas)} plazas en total, {nuevas} nuevas.")


if __name__ == "__main__":
    main()
