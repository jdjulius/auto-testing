"""Normalización de rutas y enmascarado de datos sensibles."""

from __future__ import annotations

import json
import re
from urllib.parse import parse_qsl, urlsplit

# Segmentos de ruta que son identificadores y no parte del endpoint.
_IDENTIFICADORES = [
    re.compile(r"\d+"),                                                   # 42
    re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I),  # UUID
    re.compile(r"[0-9A-HJKMNP-TV-Z]{26}", re.I),                          # ULID
    re.compile(r"[0-9a-f]{16,}", re.I),                                   # hash / ObjectId
    re.compile(r"(?=.*\d)[A-Za-z0-9_-]{20,}"),                            # token largo con dígitos
    re.compile(r"[A-Za-z]{1,5}-?\d{5,}"),                                 # INV-2024000001
]

# Palabras que hacen sensible una clave (headers, cuerpos JSON y query params).
# Se compara por palabra: "shipping" no es "pin" ni "discard" es "card".
_PALABRAS_SENSIBLES = {
    "password", "passwd", "pwd", "pass", "secret", "token", "authorization", "cookie",
    "session", "credential", "credentials", "card", "cvv", "cvc", "iban", "pin", "otp", "totp",
}
MASCARA = "***"


def _palabras(clave: str) -> list[str]:
    return [p.lower() for p in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", clave)]


def es_sensible(clave: str) -> bool:
    palabras = _palabras(clave)
    if any(p in _PALABRAS_SENSIBLES for p in palabras):
        return True
    return any(a == "api" and b == "key" for a, b in zip(palabras, palabras[1:])) or "apikey" in palabras


def es_identificador(segmento: str) -> bool:
    return any(p.fullmatch(segmento) for p in _IDENTIFICADORES)


def _nombre_parametro(anterior: str, usados: set[str]) -> str:
    """'products' -> 'productId' (como suelen nombrarlos las especificaciones OpenAPI)."""
    base = re.sub(r"[^A-Za-z0-9]", "", anterior)
    if base.endswith("ies"):
        base = base[:-3] + "y"
    elif base.endswith("s") and not base.endswith("ss"):
        base = base[:-1]
    nombre = f"{base}Id" if base else "id"
    n, candidato = 2, nombre
    while candidato in usados:
        candidato, n = f"{nombre}{n}", n + 1
    return candidato


def plantilla_ruta(ruta: str) -> tuple[str, dict[str, str]]:
    """'/carts/01M4.../product/01M5...' -> ('/carts/{cartId}/product/{productId}', {valores})."""
    segmentos = ruta.split("/")
    params: dict[str, str] = {}
    for i, seg in enumerate(segmentos):
        if seg and es_identificador(seg):
            nombre = _nombre_parametro(segmentos[i - 1] if i else "", set(params))
            params[nombre] = seg
            segmentos[i] = "{" + nombre + "}"
    return "/".join(segmentos) or "/", params


def partir_url(url: str) -> dict:
    partes = urlsplit(url)
    plantilla, path_params = plantilla_ruta(partes.path)
    return {
        "esquema": partes.scheme,
        "host": partes.netloc,
        "ruta_real": partes.path,
        "ruta": plantilla,
        "path_params": path_params,
        "query_params": dict(parse_qsl(partes.query, keep_blank_values=True)),
    }


def enmascarar(valor, clave: str = ""):
    """Copia de `valor` (dict, lista o texto) con los datos sensibles reemplazados."""
    if clave and es_sensible(clave):
        if isinstance(valor, str) and valor.lower().startswith(("bearer ", "basic ")):
            return valor.split(" ", 1)[0] + " " + MASCARA
        return MASCARA if valor not in (None, "") else valor
    if isinstance(valor, dict):
        return {k: enmascarar(v, k) for k, v in valor.items()}
    if isinstance(valor, list):
        return [enmascarar(v, clave) for v in valor]
    return valor


def cuerpo(texto: str | bytes | None, content_type: str = "", limite: int = 65_536):
    """Interpreta un cuerpo HTTP: JSON como objeto, texto truncado, binario como resumen."""
    if texto in (None, b"", ""):
        return None
    if isinstance(texto, bytes):
        if not _es_texto(content_type):
            return f"<binario {len(texto)} bytes>"
        texto = texto.decode("utf-8", errors="replace")
    try:
        return json.loads(texto)
    except ValueError:
        return texto if len(texto) <= limite else texto[:limite] + f"… <{len(texto)} caracteres>"


def _es_texto(content_type: str) -> bool:
    ct = (content_type or "").lower()
    return not ct or any(t in ct for t in ("json", "text", "xml", "javascript", "x-www-form-urlencoded"))


def campos(valor) -> list[str]:
    """Claves de primer nivel de un cuerpo JSON (para el catálogo)."""
    if isinstance(valor, dict):
        return sorted(valor)
    if isinstance(valor, list) and valor and isinstance(valor[0], dict):
        return sorted(valor[0])
    return []
