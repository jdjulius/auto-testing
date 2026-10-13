"""Mapa de pantallas de Toolshop: ruta (expresión regular), nombre y componentes (data-test).

`pantalla_de_ruta` la usa la captura de APIs para saber en qué pantalla se hizo cada llamada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pantalla:
    clave: str
    nombre: str
    ruta: str            # expresión regular sobre la ruta de la URL
    ejemplo: str         # ruta concreta para abrirla en las pruebas
    titulo: str | None = None
    componentes: dict[str, str] = field(default_factory=dict)
    requiere_sesion: bool = False


PANTALLAS = [
    Pantalla(
        "catalogo", "Catálogo (Home)", r"/", "/",
        componentes={
            "Buscador": "search-query", "Botón buscar": "search-submit", "Ordenar": "sort",
            "Filtros": "filters", "Nombre de producto": "product-name",
            "Precio de producto": "product-price", "Página siguiente": "pagination-next",
        },
    ),
    Pantalla(
        "categoria", "Categoría", r"/category/[^/]+", "/category/hand-tools", titulo="Category: Hand Tools",
        componentes={"Título": "page-title", "Ordenar": "sort", "Nombre de producto": "product-name"},
    ),
    Pantalla(
        "detalle", "Detalle de producto", r"/product/[^/]+", "",
        componentes={
            "Nombre": "product-name", "Precio": "unit-price", "Descripción": "product-description",
            "Cantidad": "quantity", "Agregar al carrito": "add-to-cart",
            "Agregar a favoritos": "add-to-favorites",
        },
    ),
    Pantalla(
        "checkout", "Checkout", r"/checkout", "/checkout",
        componentes={"Total del carrito": "cart-total", "Continuar": "proceed-1"},
    ),
    Pantalla(
        "login", "Login", r"/auth/login", "/auth/login",
        componentes={
            "Email": "email", "Contraseña": "password", "Botón login": "login-submit",
            "Registrarse": "register-link", "Olvidé mi contraseña": "forgot-password-link",
        },
    ),
    Pantalla("registro", "Registro", r"/auth/register", "/auth/register",
             componentes={"Nombre": "first-name", "Apellido": "last-name", "Email": "email",
                          "Contraseña": "password", "Botón registrar": "register-submit"}),
    Pantalla("olvido-clave", "Olvidé mi contraseña", r"/auth/forgot-password", "/auth/forgot-password",
             componentes={"Email": "email", "Botón enviar": "forgot-password-submit"}),
    Pantalla("contacto", "Contacto", r"/contact", "/contact",
             componentes={"Nombre": "first-name", "Apellido": "last-name", "Email": "email",
                          "Asunto": "subject", "Mensaje": "message", "Enviar": "contact-submit"}),
    Pantalla("cuenta", "Mi cuenta", r"/account", "/account", titulo="My account",
             componentes={"Título": "page-title", "Favoritos": "nav-favorites", "Perfil": "nav-profile",
                          "Facturas": "nav-invoices", "Mensajes": "nav-messages"},
             requiere_sesion=True),
    Pantalla("perfil", "Perfil", r"/account/profile", "/account/profile", requiere_sesion=True,
             componentes={"Nombre": "first-name", "Apellido": "last-name", "Email": "email"}),
    Pantalla("favoritos", "Favoritos", r"/account/favorites", "/account/favorites", requiere_sesion=True),
    Pantalla("facturas", "Facturas", r"/account/invoices", "/account/invoices", requiere_sesion=True),
    Pantalla("mensajes", "Mensajes", r"/account/messages", "/account/messages", requiere_sesion=True),
]

_POR_RUTA = [(re.compile(rf"^{p.ruta}/?$"), p) for p in PANTALLAS]


def pantalla_de_ruta(ruta: str) -> str:
    """'/product/01M4...' -> 'Detalle de producto'. Rutas desconocidas: la ruta misma."""
    for patron, pantalla in _POR_RUTA:
        if patron.match(ruta):
            return pantalla.nombre
    return ruta
