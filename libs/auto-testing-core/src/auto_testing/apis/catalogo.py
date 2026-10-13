"""Catálogo incremental de las APIs que consume la UI.

Archivos en ``<sitio>/reportes/apis/``:

- ``endpoints.csv`` / ``endpoints.xlsx``: un endpoint por fila (método + host + ruta
  normalizada), con sus parámetros, headers, status, pantallas y escenarios.
- ``muestras/API-XXXX.json``: ejemplos reales de request y response (enmascarados),
  uno por combinación distinta de status, pantalla y parámetros.
- ``llamadas.csv``: historial, una fila por llamada observada (solo crece).
- ``no_documentados.csv`` y ``no_consumidos.csv``: comparación contra el OpenAPI,
  si el sitio lo configura.
"""

from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from auto_testing.registro import ahora, texto_csv

PREFIJO = "API-"
SEP = " | "  # separador de listas dentro de una celda (no usa ',' ni ';')
MAX_MUESTRAS = 5

# Headers que agrega el navegador y no describen al endpoint.
HEADERS_RUIDO = {
    "accept-encoding", "accept-language", "connection", "host", "origin", "referer",
    "user-agent", "sec-fetch-dest", "sec-fetch-mode", "sec-fetch-site", "priority",
    "content-length", "cache-control", "pragma", "dnt",
}


@dataclass
class Endpoint:
    id: str
    tipo: str            # propio | tercero
    metodo: str
    host: str
    ruta: str
    path_params: str = ""
    query_params: str = ""
    body_campos: str = ""
    headers_request: str = ""
    content_type_request: str = ""
    content_type_response: str = ""
    status: str = ""
    pantallas: str = ""
    escenarios: str = ""
    llamadas: int = 0
    duracion_ms_prom: float = 0.0
    documentado: str = ""   # sí | no | (vacío si no hay OpenAPI)
    fecha_alta: str = ""
    ultima_vez: str = ""

    @property
    def clave(self) -> tuple[str, str, str]:
        return (self.metodo, self.host, self.ruta)


COLUMNAS = [f.name for f in fields(Endpoint)]
COLUMNAS_LLAMADAS = ["run_id", "fecha", "api_id", "metodo", "url", "status", "duracion_ms",
                     "pantalla", "escenario_id"]


def _lista(texto: str) -> list[str]:
    return [x for x in (texto or "").split(SEP) if x]


def _unir(texto: str, nuevos) -> str:
    valores = _lista(texto)
    for v in nuevos:
        v = str(v)
        if v and v not in valores:
            valores.append(v)
    return SEP.join(sorted(valores, key=str.lower))


def _escribir_atomico(ruta: Path, escribir) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=ruta.parent, prefix=f".{ruta.stem}", suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
        escribir(f)
    os.replace(tmp, ruta)


class CatalogoApis:
    def __init__(self, carpeta: Path) -> None:
        self.carpeta = Path(carpeta)
        self.ruta_csv = self.carpeta / "endpoints.csv"
        self.ruta_muestras = self.carpeta / "muestras"
        self.ruta_llamadas = self.carpeta / "llamadas.csv"
        self.endpoints: dict[tuple[str, str, str], Endpoint] = {}
        self.nuevos: list[Endpoint] = []
        self._muestras: dict[str, list[dict]] = {}
        self._llamadas: list[dict] = []
        self._cargar()

    # ---------------------------------------------------------------- lectura
    def _cargar(self) -> None:
        if not self.ruta_csv.exists():
            return
        with self.ruta_csv.open(newline="", encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                fila["llamadas"] = int(fila.get("llamadas") or 0)
                fila["duracion_ms_prom"] = float(fila.get("duracion_ms_prom") or 0)
                ep = Endpoint(**{c: fila.get(c, "") for c in COLUMNAS})
                self.endpoints[ep.clave] = ep

    def muestras(self, api_id: str) -> list[dict]:
        if api_id not in self._muestras:
            ruta = self.ruta_muestras / f"{api_id}.json"
            self._muestras[api_id] = json.loads(ruta.read_text("utf-8")) if ruta.exists() else []
        return self._muestras[api_id]

    # ---------------------------------------------------------------- registro
    def _siguiente_id(self) -> str:
        nums = [int(m.group(1)) for e in self.endpoints.values()
                if (m := re.fullmatch(rf"{PREFIJO}(\d+)", e.id))]
        return f"{PREFIJO}{max(nums, default=0) + 1:04d}"

    def registrar(self, llamada: dict, *, run_id: str = "") -> Endpoint:
        """Agrega una llamada observada (ver `captura.py` para el formato)."""
        req, resp = llamada["request"], llamada["response"]
        clave = (req["metodo"], req["host"], req["ruta"])
        ep = self.endpoints.get(clave)
        if ep is None:
            ep = Endpoint(id=self._siguiente_id(), tipo=llamada["tipo"], metodo=req["metodo"],
                          host=req["host"], ruta=req["ruta"], fecha_alta=ahora())
            self.endpoints[clave] = ep
            self.nuevos.append(ep)

        ep.path_params = _unir(ep.path_params, req["path_params"])
        ep.query_params = _unir(ep.query_params, req["query_params"])
        ep.body_campos = _unir(ep.body_campos, llamada.get("body_campos", []))
        ep.headers_request = _unir(
            ep.headers_request, (h for h in req["headers"] if h.lower() not in HEADERS_RUIDO))
        ep.content_type_request = _unir(ep.content_type_request, [req.get("content_type", "")])
        ep.content_type_response = _unir(ep.content_type_response, [resp.get("content_type", "")])
        ep.status = _unir(ep.status, [resp.get("status", "")])
        ep.pantallas = _unir(ep.pantallas, [llamada.get("pantalla", "")])
        ep.escenarios = _unir(ep.escenarios, [llamada.get("escenario_id", "")])
        duracion = float(resp.get("duracion_ms") or 0)
        ep.duracion_ms_prom = round((ep.duracion_ms_prom * ep.llamadas + duracion) / (ep.llamadas + 1), 1)
        ep.llamadas += 1
        ep.ultima_vez = llamada.get("fecha") or ahora()

        self._agregar_muestra(ep.id, llamada)
        self._llamadas.append({
            "run_id": run_id, "fecha": ep.ultima_vez, "api_id": ep.id, "metodo": ep.metodo,
            "url": req["url"], "status": resp.get("status", ""), "duracion_ms": duracion,
            "pantalla": llamada.get("pantalla", ""), "escenario_id": llamada.get("escenario_id", ""),
        })
        return ep

    def _agregar_muestra(self, api_id: str, llamada: dict) -> None:
        """Guarda una muestra por cada combinación distinta; la más reciente reemplaza a la anterior."""
        firma = [
            llamada["response"].get("status"),
            llamada.get("pantalla"),
            sorted(llamada["request"]["query_params"]),
            sorted(llamada.get("body_campos", [])),
        ]
        muestras = [m for m in self.muestras(api_id) if m.get("_firma") != firma]
        muestras.insert(0, {"_firma": firma, **llamada})
        self._muestras[api_id] = muestras[:MAX_MUESTRAS]

    # ---------------------------------------------------------------- OpenAPI
    def comparar_openapi(self, especificacion: dict, hosts_propios: list[str]) -> tuple[list, list]:
        """Marca cada endpoint propio como documentado o no, y lista lo documentado que la UI no usa."""
        documentadas = set()
        for ruta, operaciones in (especificacion.get("paths") or {}).items():
            for metodo in operaciones:
                if metodo.lower() in {"get", "post", "put", "patch", "delete", "head", "options", "query"}:
                    documentadas.add((metodo.upper(), _forma(ruta)))
        base = _ruta_base(especificacion)
        vistos = set()
        no_documentados = []
        for ep in self.endpoints.values():
            if ep.tipo != "propio":
                continue
            forma = (ep.metodo, _forma(ep.ruta.removeprefix(base) or "/"))
            vistos.add(forma)
            ep.documentado = "sí" if forma in documentadas else "no"
            if ep.documentado == "no":
                no_documentados.append(ep)
        no_consumidos = sorted(documentadas - vistos, key=lambda x: (x[1], x[0]))
        return no_documentados, no_consumidos

    # ---------------------------------------------------------------- escritura
    def guardar(self, no_consumidos: list | None = None, no_documentados: list | None = None) -> None:
        orden = sorted(self.endpoints.values(), key=lambda e: e.id)

        def escribir(f):
            w = csv.DictWriter(f, fieldnames=COLUMNAS)
            w.writeheader()
            for ep in orden:
                w.writerow({k: texto_csv(v) for k, v in asdict(ep).items()})
        _escribir_atomico(self.ruta_csv, escribir)

        for api_id, muestras in self._muestras.items():
            ruta = self.ruta_muestras / f"{api_id}.json"
            _escribir_atomico(ruta, lambda f, d=muestras: json.dump(d, f, ensure_ascii=False, indent=2))

        if self._llamadas:
            nuevo = not self.ruta_llamadas.exists()
            self.ruta_llamadas.parent.mkdir(parents=True, exist_ok=True)
            with self.ruta_llamadas.open("a", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=COLUMNAS_LLAMADAS)
                if nuevo:
                    w.writeheader()
                for fila in self._llamadas:
                    w.writerow({k: texto_csv(v) for k, v in fila.items()})
            self._llamadas.clear()

        if no_consumidos is not None:
            def escribir_nc(f):
                w = csv.writer(f)
                w.writerow(["metodo", "ruta"])
                w.writerows(no_consumidos)
            _escribir_atomico(self.carpeta / "no_consumidos.csv", escribir_nc)
        if no_documentados is not None:
            def escribir_nd(f):
                w = csv.writer(f)
                w.writerow(["id", "metodo", "ruta", "pantallas"])
                w.writerows([[e.id, e.metodo, e.ruta, texto_csv(e.pantallas)] for e in no_documentados])
            _escribir_atomico(self.carpeta / "no_documentados.csv", escribir_nd)

        self._guardar_excel(orden)

    def _guardar_excel(self, orden: list[Endpoint]) -> None:
        try:
            from auto_testing.excel import exportar_tabla
        except ImportError:
            return
        columnas = {
            "id": ("ID", 10), "tipo": ("Tipo", 9), "metodo": ("Método", 9), "host": ("Host", 30),
            "ruta": ("Endpoint", 42), "pantallas": ("Pantallas", 34), "status": ("Status", 12),
            "path_params": ("Path params", 22), "query_params": ("Query params", 34),
            "body_campos": ("Campos del body", 34), "headers_request": ("Headers", 30),
            "content_type_request": ("Content-Type request", 22),
            "content_type_response": ("Content-Type response", 22),
            "escenarios": ("Escenarios", 30), "llamadas": ("Llamadas", 10),
            "duracion_ms_prom": ("Duración prom. (ms)", 12), "documentado": ("En OpenAPI", 11),
            "fecha_alta": ("Fecha de alta", 20), "ultima_vez": ("Última vez", 20),
        }
        exportar_tabla(
            self.ruta_csv.with_suffix(".xlsx"),
            [{k: texto_csv(v) for k, v in asdict(e).items()} for e in orden],
            columnas, hoja="Endpoints",
            colores={"tipo": {"propio": "C6EFCE", "tercero": "F2F2F2"},
                     "documentado": {"sí": "C6EFCE", "no": "FFC7CE"}},
            ajustar=("pantallas", "query_params", "body_campos", "headers_request", "escenarios"),
        )


def _forma(ruta: str) -> str:
    """'/products/{productId}' y '/products/{id}' tienen la misma forma."""
    return re.sub(r"\{[^}]+\}", "{}", ruta.rstrip("/") or "/")


def _ruta_base(especificacion: dict) -> str:
    """Prefijo de ruta del primer servidor del OpenAPI (p. ej. '/api/v1')."""
    from urllib.parse import urlsplit

    servidores = especificacion.get("servers") or []
    return urlsplit(servidores[0]["url"]).path.rstrip("/") if servidores else ""
