"""Cliente HTTP de la API: centraliza URL base, token, tiempos y evidencias.

Cada petición queda como un paso de Allure con el request y el response
adjuntos (con los datos sensibles enmascarados).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

try:
    import allure
except ImportError:  # el proyecto funciona sin Allure
    allure = None

ESQUEMAS = Path(__file__).resolve().parents[1] / "esquemas"
_SENSIBLES = {"password", "access_token", "authorization", "token", "cookie", "set-cookie"}


def _enmascarar(datos):
    if isinstance(datos, dict):
        return {k: "***" if k.lower() in _SENSIBLES else _enmascarar(v) for k, v in datos.items()}
    if isinstance(datos, list):
        return [_enmascarar(v) for v in datos]
    return datos


class ClienteApi:
    def __init__(self, base_url: str, timeout: float = 30, token: str | None = None) -> None:
        self.base_url = base_url
        self._http = httpx.Client(base_url=base_url, timeout=timeout,
                                  headers={"Accept": "application/json"})
        self.token = token

    def con_token(self, token: str) -> "ClienteApi":
        """Copia del cliente que envía 'Authorization: Bearer <token>'."""
        return ClienteApi(self.base_url, self._http.timeout.read or 30, token)

    def cerrar(self) -> None:
        self._http.close()

    def request(self, metodo: str, ruta: str, **kwargs) -> httpx.Response:
        headers = dict(kwargs.pop("headers", {}) or {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")
        titulo = f"{metodo} {ruta}"
        if allure is None:
            return self._http.request(metodo, ruta, headers=headers, **kwargs)
        with allure.step(titulo):
            respuesta = self._http.request(metodo, ruta, headers=headers, **kwargs)
            self._adjuntar(respuesta, kwargs)
            return respuesta

    def get(self, ruta: str, **kw) -> httpx.Response:
        return self.request("GET", ruta, **kw)

    def post(self, ruta: str, **kw) -> httpx.Response:
        return self.request("POST", ruta, **kw)

    def put(self, ruta: str, **kw) -> httpx.Response:
        return self.request("PUT", ruta, **kw)

    def delete(self, ruta: str, **kw) -> httpx.Response:
        return self.request("DELETE", ruta, **kw)

    def query(self, ruta: str, **kw) -> httpx.Response:
        """Método HTTP QUERY (lo usa la UI de Toolshop para listar y buscar)."""
        return self.request("QUERY", ruta, **kw)

    @staticmethod
    def _adjuntar(respuesta: httpx.Response, kwargs: dict) -> None:
        req = respuesta.request
        try:
            cuerpo_req = json.loads(req.content) if req.content else None
        except ValueError:
            cuerpo_req = req.content.decode("utf-8", "replace")
        try:
            cuerpo_resp = respuesta.json()
        except ValueError:
            cuerpo_resp = respuesta.text[:5000]
        evidencia = {
            "request": {"metodo": req.method, "url": str(req.url),
                        "headers": _enmascarar(dict(req.headers)), "body": _enmascarar(cuerpo_req)},
            "response": {"status": respuesta.status_code,
                         "duracion_ms": round(respuesta.elapsed.total_seconds() * 1000, 1),
                         "headers": _enmascarar(dict(respuesta.headers)), "body": _enmascarar(cuerpo_resp)},
        }
        allure.attach(json.dumps(evidencia, ensure_ascii=False, indent=2),
                      name=f"{req.method} {req.url.path} → {respuesta.status_code}",
                      attachment_type=allure.attachment_type.JSON)


def _registro() -> Registry:
    """Todos los esquemas, para que '$ref': 'producto.json' se resuelva entre archivos."""
    recursos = []
    for archivo in ESQUEMAS.glob("*.json"):
        contenido = json.loads(archivo.read_text("utf-8"))
        contenido.setdefault("$id", archivo.name)
        recursos.append((archivo.name, Resource.from_contents(contenido)))
    return Registry().with_resources(recursos)


def validar_esquema(datos, nombre: str) -> None:
    """Valida `datos` contra esquemas/<nombre>.json y muestra todos los errores juntos."""
    registro = _registro()
    esquema = registro[f"{nombre}.json"].contents
    validador = Draft202012Validator(esquema, registry=registro)
    errores = sorted(validador.iter_errors(datos), key=lambda e: list(e.path))
    assert not errores, f"La respuesta no cumple el esquema '{nombre}':\n" + "\n".join(
        f"  - {'/'.join(map(str, e.path)) or '(raíz)'}: {e.message}" for e in errores[:20])
