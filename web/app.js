"use strict";

// Publicada: data/plazas.json junto a index.html. En local: ../data/plazas.json
const DATA_URLS = ["data/plazas.json", "../data/plazas.json"];
const DIAS_NUEVA = 7;
const DIAS_PRONTO = 5;

const ETIQ_TIPO = { oposicion: "Oposición", concurso: "Concurso", "concurso-oposicion": "Concurso-oposición", bolsa: "Bolsa", otro: "Otro" };
const ETIQ_AMBITO = { estatal: "Estatal", autonomico: "Autonómico", provincial: "Provincial", local: "Local", universidad: "Universidad", otro: "Otro" };
const ETIQ_ESTADO = { abierto: "Abierta", cerrado: "Cerrada", desconocido: "Plazo desconocido" };

const $ = (id) => document.getElementById(id);
let plazas = [];
const hoy = new Date(new Date().toDateString());

const fecha = (s) => (s ? new Date(s + "T00:00:00") : null);
const dias = (a, b) => Math.round((a - b) / 86400000);
const fmt = (s) => (s ? fecha(s).toLocaleDateString("es-ES", { day: "numeric", month: "short", year: "numeric" }) : "—");
const norm = (s) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// Estado calculado en el navegador, para que no quede obsoleto entre ejecuciones del scraper
function estadoActual(p) {
  if (!p.fecha_limite) return "desconocido";
  return fecha(p.fecha_limite) >= hoy ? "abierto" : "cerrado";
}
const esNueva = (p) => dias(hoy, fecha(p.fecha_publicacion)) <= DIAS_NUEVA;
const cierraPronto = (p) => estadoActual(p) === "abierto" && dias(fecha(p.fecha_limite), hoy) <= DIAS_PRONTO;

function rellenar(select, valores, etiquetas) {
  [...new Set(valores.filter(Boolean))].sort().forEach((v) => {
    const o = el("option", null, (etiquetas && etiquetas[v]) || v);
    o.value = v;
    select.appendChild(o);
  });
}

function resumen(lista) {
  const abiertas = lista.filter((p) => estadoActual(p) === "abierto");
  const datos = [
    [abiertas.length, "plazas abiertas"],
    [abiertas.reduce((s, p) => s + (p.num_plazas || 0), 0), "puestos convocados (abiertas)"],
    [lista.filter(esNueva).length, "nuevas esta semana"],
    [lista.filter(cierraPronto).length, `cierran en ${DIAS_PRONTO} días o menos`],
  ];
  const cont = $("resumen");
  cont.replaceChildren(...datos.map(([n, t]) => { const d = el("div", "dato"); d.append(el("b", null, n), el("span", null, t)); return d; }));
}

function tarjeta(p) {
  const li = el("li", "plaza");
  const est = estadoActual(p);
  const et = el("div", "etiquetas");
  et.appendChild(el("span", "et " + est, ETIQ_ESTADO[est]));
  if (esNueva(p)) et.appendChild(el("span", "et nueva", "Nueva"));
  if (cierraPronto(p)) {
    const d = dias(fecha(p.fecha_limite), hoy);
    et.appendChild(el("span", "et pronto", d === 0 ? "Cierra hoy" : `Cierra en ${d} día${d === 1 ? "" : "s"}`));
  }
  const meta = el("ul", "meta");
  [
    ETIQ_TIPO[p.tipo_proceso] || "—",
    ETIQ_AMBITO[p.ambito] || "—",
    p.provincia || "Provincia sin determinar",
    p.num_plazas ? `${p.num_plazas} plaza${p.num_plazas === 1 ? "" : "s"}` : "Nº de plazas no detectado",
    `Publicada: ${fmt(p.fecha_publicacion)}`,
    p.fecha_limite ? `Límite (estimado): ${fmt(p.fecha_limite)}` : "Límite: consultar bases",
  ].forEach((t) => meta.appendChild(el("li", null, t)));

  const a = el("a", "ver", "Ver publicación oficial →");
  a.href = p.url_oficial;
  a.target = "_blank";
  a.rel = "noopener noreferrer";

  li.append(et, el("p", "org", p.organismo), el("h2", null, p.titulo), meta, a);
  return li;
}

function ordenar(lista, modo) {
  const inf = Infinity;
  const cierre = (p) => (p.fecha_limite ? fecha(p.fecha_limite).getTime() : inf);
  const abierta = (p) => estadoActual(p) === "abierto";
  const fns = {
    cierre: (a, b) => (abierta(b) - abierta(a)) || cierre(a) - cierre(b),
    reciente: (a, b) => b.fecha_publicacion.localeCompare(a.fecha_publicacion),
    plazas: (a, b) => (b.num_plazas || 0) - (a.num_plazas || 0),
  };
  return [...lista].sort(fns[modo]);
}

function render() {
  const q = norm($("q").value);
  const fp = $("f-provincia").value, fa = $("f-ambito").value, ft = $("f-tipo").value, fe = $("f-estado").value;
  const filtradas = plazas.filter((p) =>
    (!fp || p.provincia === fp) && (!fa || p.ambito === fa) && (!ft || p.tipo_proceso === ft) &&
    (!fe || estadoActual(p) === fe) && (!q || norm(`${p.titulo} ${p.organismo} ${p.provincia}`).includes(q)));
  const ord = ordenar(filtradas, $("orden").value);
  $("lista").replaceChildren(...ord.map(tarjeta));
  $("vacio").hidden = ord.length > 0;
  $("contador").textContent = `${ord.length} de ${plazas.length} convocatorias`;
}

async function init() {
  try {
    let r = null;
    for (const url of DATA_URLS) {
      r = await fetch(url, { cache: "no-store" });
      if (r.ok) break;
    }
    if (!r.ok) throw new Error("HTTP " + r.status);
    const d = await r.json();
    plazas = d.plazas;
    $("actualizado").textContent = "Actualizado: " + new Date(d.actualizado).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" });
    rellenar($("f-provincia"), plazas.map((p) => p.provincia));
    rellenar($("f-ambito"), plazas.map((p) => p.ambito), ETIQ_AMBITO);
    rellenar($("f-tipo"), plazas.map((p) => p.tipo_proceso), ETIQ_TIPO);
    resumen(plazas);
    ["q", "f-provincia", "f-ambito", "f-tipo", "f-estado", "orden"].forEach((id) => $(id).addEventListener("input", render));
    render();
  } catch (e) {
    const err = $("error");
    err.hidden = false;
    err.textContent = "No se pudieron cargar los datos (" + e.message + "). Abre la web desde un servidor local, no con doble clic.";
  }
}
init();
