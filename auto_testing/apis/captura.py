"""Captura de las llamadas a APIs que hace la página durante una prueba de UI.

Se engancha al contexto de Playwright de la prueba:

- en el evento ``request`` anota la **pantalla** (la ruta de la página en el momento
  en que sale la petición: en una SPA la ruta puede cambiar antes de la respuesta);
- al terminar la prueba (antes de cerrar el navegador) lee request y response,
  normaliza la ruta, enmascara datos sensibles y devuelve las llamadas.
"""

from __future__ import annotations

import fnmatch
import re
from datetime import datetime
from urllib.parse import urlsplit

from auto_testing.apis import normalizar

TIPOS_RECURSO = {"xhr", "fetch"}


class ConfigCaptura:
    def __init__(self, hosts_propios=(), excluir=(), resolver_pantalla=None) -> None:
        self.hosts_propios = [h.strip() for h in hosts_propios if h.strip()]
        self.excluir = [re.compile(p) for p in excluir if p.strip()]
        self.resolver_pantalla = resolver_pantalla

    def tipo(self, host: str) -> str:
        return "propio" if any(fnmatch.fnmatch(host, h) for h in self.hosts_propios) else "tercero"

    def excluida(self, url: str) -> bool:
        return any(p.search(url) for p in self.excluir)

    def pantalla(self, url_pagina: str) -> str:
        ruta = urlsplit(url_pagina).path or "/"
        if self.resolver_pantalla:
            try:
                nombre = self.resolver_pantalla(ruta)
                if nombre:
                    return nombre
            except Exception:
                pass
        return normalizar.plantilla_ruta(ruta)[0]


class CapturaPrueba:
    """Llamadas de una prueba. Uso: iniciar(contexto) ... terminar() -> list[dict]."""

    def __init__(self, config: ConfigCaptura, escenario_id: str = "", nodeid: str = "") -> None:
        self.config = config
        self.escenario_id = escenario_id
        self.nodeid = nodeid
        self._pendientes: list[tuple] = []
        self._terminadas: set[int] = set()
        self._fallidas: dict[int, str] = {}
        self._contexto = None

    def iniciar(self, contexto) -> None:
        self._contexto = contexto
        contexto.on("request", self._al_salir)
        contexto.on("requestfinished", self._al_terminar)
        contexto.on("requestfailed", self._al_fallar)

    def _al_terminar(self, request) -> None:
        self._terminadas.add(id(request))

    def _al_fallar(self, request) -> None:
        self._fallidas[id(request)] = request.failure or "falló"

    def _al_salir(self, request) -> None:
        if request.resource_type not in TIPOS_RECURSO or self.config.excluida(request.url):
            return
        try:
            url_pagina = request.frame.url
        except Exception:
            url_pagina = ""
        self._pendientes.append((request, url_pagina, datetime.now().isoformat(timespec="seconds")))

    def terminar(self) -> list[dict]:
        if self._contexto is not None:
            for evento, funcion in (("request", self._al_salir), ("requestfinished", self._al_terminar),
                                    ("requestfailed", self._al_fallar)):
                try:
                    self._contexto.remove_listener(evento, funcion)
                except Exception:
                    pass
        llamadas = []
        for request, url_pagina, fecha in self._pendientes:
            llamada = self._leer(request, url_pagina, fecha)
            if llamada:
                llamadas.append(llamada)
        self._pendientes.clear()
        return llamadas

    def _leer(self, request, url_pagina: str, fecha: str) -> dict | None:
        partes = normalizar.partir_url(request.url)
        try:
            headers_req = request.all_headers()
        except Exception:
            headers_req = dict(request.headers)
        ct_req = headers_req.get("content-type", "")
        body_req = normalizar.cuerpo(request.post_data, ct_req)
        # Solo se leen las respuestas de peticiones terminadas: en Playwright síncrono
        # response() espera, y una conexión que no termina (streaming, SSE) bloquearía.
        respuesta = _respuesta(request) if id(request) in self._terminadas else None
        status, headers_resp, body_resp = "", {}, None
        if respuesta is not None:
            status = respuesta.status
            try:
                headers_resp = respuesta.all_headers()
            except Exception:
                headers_resp = dict(respuesta.headers)
            try:
                body_resp = normalizar.cuerpo(respuesta.body(), headers_resp.get("content-type", ""))
            except Exception:
                body_resp = None
        elif id(request) in self._fallidas:
            status = f"falló: {self._fallidas[id(request)]}"
        else:
            status = "pendiente"
        return {
            "fecha": fecha,
            "tipo": self.config.tipo(partes["host"]),
            "pantalla": self.config.pantalla(url_pagina),
            "url_pagina": url_pagina,
            "escenario_id": self.escenario_id,
            "nodeid": self.nodeid,
            "body_campos": normalizar.campos(body_req),
            "request": {
                "metodo": request.method,
                "url": _url_enmascarada(request.url, partes),
                "host": partes["host"],
                "ruta": partes["ruta"],
                "ruta_real": partes["ruta_real"],
                "path_params": partes["path_params"],
                "query_params": normalizar.enmascarar(partes["query_params"]),
                "headers": normalizar.enmascarar(headers_req),
                "content_type": ct_req.split(";")[0],
                "body": normalizar.enmascarar(body_req),
            },
            "response": {
                "status": status,
                "headers": normalizar.enmascarar(headers_resp),
                "content_type": headers_resp.get("content-type", "").split(";")[0],
                "duracion_ms": _duracion(request),
                "body": normalizar.enmascarar(body_resp),
            },
        }


def _respuesta(request):
    try:
        return request.response()
    except Exception:
        return None


def _duracion(request) -> float:
    try:
        fin = request.timing.get("responseEnd", -1)  # ms desde que salió la petición
        if fin > 0:
            return round(fin, 1)
    except Exception:
        pass
    return 0.0


def _url_enmascarada(url: str, partes: dict) -> str:
    """La URL tal como se guardará: con los query params sensibles enmascarados."""
    from urllib.parse import urlencode

    query = normalizar.enmascarar(partes["query_params"])
    base = url.split("?", 1)[0]
    return f"{base}?{urlencode(query)}" if query else base
