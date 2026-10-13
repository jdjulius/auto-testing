"""Mapa de pantallas de saucedemo: ruta, título y componentes (data-test).

Es la fuente de verdad del levantamiento de pantallas: ``tests/ui/test_pantallas.py``
genera un escenario por pantalla que verifica que todos sus componentes existan.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pantalla:
    clave: str
    nombre: str
    ruta: str
    titulo: str | None
    # nombre legible -> valor de data-test
    componentes: dict[str, str] = field(default_factory=dict)
    # componentes que aparecen varias veces: nombre -> (data-test, cantidad esperada)
    repetidos: dict[str, tuple[str, int]] = field(default_factory=dict)


PANTALLAS = [
    Pantalla(
        clave="login",
        nombre="Login",
        ruta="/",
        titulo=None,
        componentes={
            "Usuario": "username",
            "Contraseña": "password",
            "Botón Login": "login-button",
            "Lista de usuarios aceptados": "login-credentials",
            "Contraseña de todos los usuarios": "login-password",
        },
    ),
    Pantalla(
        clave="inventario",
        nombre="Inventario (Products)",
        ruta="/inventory.html",
        titulo="Products",
        componentes={
            "Título": "title",
            "Menú lateral": "open-menu",
            "Carrito": "shopping-cart-link",
            "Ordenamiento": "product-sort-container",
            "Lista de productos": "inventory-list",
            "Pie de página": "footer",
            "Copyright": "footer-copy",
        },
        repetidos={
            "Producto": ("inventory-item", 6),
            "Nombre de producto": ("inventory-item-name", 6),
            "Descripción de producto": ("inventory-item-desc", 6),
            "Precio de producto": ("inventory-item-price", 6),
        },
    ),
    Pantalla(
        clave="detalle",
        nombre="Detalle de producto",
        ruta="/inventory-item.html?id=4",
        titulo=None,
        componentes={
            "Volver a productos": "back-to-products",
            "Nombre": "inventory-item-name",
            "Descripción": "inventory-item-desc",
            "Precio": "inventory-item-price",
            "Imagen": "item-sauce-labs-backpack-img",
            "Agregar al carrito": "add-to-cart",
        },
    ),
    Pantalla(
        clave="carrito",
        nombre="Carrito (Your Cart)",
        ruta="/cart.html",
        titulo="Your Cart",
        componentes={
            "Título": "title",
            "Lista del carrito": "cart-list",
            "Encabezado QTY": "cart-quantity-label",
            "Encabezado Description": "cart-desc-label",
            "Seguir comprando": "continue-shopping",
            "Checkout": "checkout",
        },
        repetidos={
            "Producto": ("inventory-item", 1),
            "Cantidad": ("item-quantity", 1),
        },
    ),
    Pantalla(
        clave="checkout-paso-1",
        nombre="Checkout paso 1 (Your Information)",
        ruta="/checkout-step-one.html",
        titulo="Checkout: Your Information",
        componentes={
            "Título": "title",
            "Nombre": "firstName",
            "Apellido": "lastName",
            "Código postal": "postalCode",
            "Cancelar": "cancel",
            "Continuar": "continue",
        },
    ),
    Pantalla(
        clave="checkout-paso-2",
        nombre="Checkout paso 2 (Overview)",
        ruta="/checkout-step-two.html",
        titulo="Checkout: Overview",
        componentes={
            "Título": "title",
            "Lista de productos": "cart-list",
            "Etiqueta de pago": "payment-info-label",
            "Medio de pago": "payment-info-value",
            "Etiqueta de envío": "shipping-info-label",
            "Medio de envío": "shipping-info-value",
            "Etiqueta de total": "total-info-label",
            "Subtotal": "subtotal-label",
            "Impuesto": "tax-label",
            "Total": "total-label",
            "Cancelar": "cancel",
            "Finalizar": "finish",
        },
        repetidos={
            "Producto": ("inventory-item", 1),
            "Cantidad": ("item-quantity", 1),
            "Precio": ("inventory-item-price", 1),
        },
    ),
    Pantalla(
        clave="checkout-completo",
        nombre="Checkout completo (Complete!)",
        ruta="/checkout-complete.html",
        titulo="Checkout: Complete!",
        componentes={
            "Título": "title",
            "Imagen Pony Express": "pony-express",
            "Encabezado de confirmación": "complete-header",
            "Texto de confirmación": "complete-text",
            "Back Home": "back-to-products",
        },
    ),
    Pantalla(
        clave="menu",
        nombre="Menú lateral",
        ruta="/inventory.html",
        titulo=None,
        componentes={
            "All Items": "inventory-sidebar-link",
            "About": "about-sidebar-link",
            "Logout": "logout-sidebar-link",
            "Reset App State": "reset-sidebar-link",
        },
    ),
]
