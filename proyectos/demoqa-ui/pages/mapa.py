"""Mapa de pantallas de DemoQA: ruta (expresión regular), nombre y componentes.

DemoQA no usa data-test/data-cy: sus componentes tienen "id" normal (a veces con
errores de tipeo reales del sitio, documentados abajo) o, cuando no hay id estable,
texto/rol. Por eso `componentes` guarda selectores Playwright completos
("#id", "text=...", "role=button[name='...']") y no solo un valor de atributo:
`tests/ui/test_pantallas.py` hace `page.locator(valor)` directamente.

Varias páginas muestran "Please select an item from left to start practice." si se
abren solo con la ruta de sección (p. ej. /elements): cada pantalla real está en la
sub-ruta (p. ej. /text-box), que es la que se registra aquí.
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
        "home", "Home (secciones)", r"/", "/",
        componentes={
            "Elements": "a[href='/elements']", "Forms": "a[href='/forms']",
            "Alerts, Frame & Windows": "a[href='/alertsWindows']", "Widgets": "a[href='/widgets']",
            "Interactions": "a[href='/interaction']", "Book Store Application": "a[href='/books']",
        },
    ),
    # --- Elements ---
    Pantalla(
        "text-box", "Text Box", r"/text-box", "/text-box",
        componentes={
            "Nombre completo": "#userName", "Email": "#userEmail",
            "Dirección actual": "#currentAddress", "Dirección permanente": "#permanentAddress",
            "Enviar": "#submit",
        },
    ),
    Pantalla(
        "checkbox", "Check Box", r"/checkbox", "/checkbox",
        # El árbol (rc-tree) no tiene ids propios: se ubica por rol y texto.
        componentes={"Casilla Home": "role=checkbox[name='Select Home']"},
    ),
    Pantalla(
        "radio-button", "Radio Button", r"/radio-button", "/radio-button",
        componentes={
            "Yes": "#yesRadio", "Impressive": "#impressiveRadio",
            "No (deshabilitado)": "#noRadio",
        },
    ),
    Pantalla(
        "webtables", "Web Tables", r"/webtables", "/webtables",
        componentes={"Agregar registro": "#addNewRecordButton", "Buscar": "#searchBox"},
    ),
    Pantalla(
        "buttons", "Buttons", r"/buttons", "/buttons",
        componentes={
            "Doble clic": "#doubleClickBtn", "Clic derecho": "#rightClickBtn",
            # El botón "Click Me" tiene un id aleatorio distinto en cada carga: usar texto.
            "Clic simple": "role=button[name='Click Me']",
        },
    ),
    Pantalla(
        "links", "Links", r"/links", "/links",
        componentes={
            "Link simple": "#simpleLink", "Link dinámico": "#dynamicLink",
            "Created (201)": "#created", "Bad Request (400)": "#bad-request",
            # "#linkResponse" no se incluye: solo aparece después de hacer clic en un link.
        },
    ),
    Pantalla(
        "broken", "Broken Links - Images", r"/broken", "/broken",
        componentes={
            "Link válido": "text=Click Here for Valid Link",
            "Link roto": "text=Click Here for Broken Link",
        },
    ),
    Pantalla(
        "upload-download", "Upload and Download", r"/upload-download", "/upload-download",
        componentes={"Descargar": "#downloadButton", "Subir archivo": "#uploadFile"},
    ),
    Pantalla(
        "dynamic-properties", "Dynamic Properties", r"/dynamic-properties", "/dynamic-properties",
        componentes={
            "Se habilita a los 5s": "#enableAfter", "Cambia de color a los 5s": "#colorChange",
        },
    ),
    # --- Forms ---
    Pantalla(
        "automation-practice-form", "Practice Form", r"/automation-practice-form", "/automation-practice-form",
        componentes={
            "Nombre": "#firstName", "Apellido": "#lastName", "Email": "#userEmail",
            "Celular": "#userNumber", "Fecha de nacimiento": "#dateOfBirthInput",
            "Dirección actual": "#currentAddress", "Subir foto": "#uploadPicture",
            "Enviar": "#submit",
        },
    ),
    # --- Alerts, Frame & Windows ---
    Pantalla(
        "browser-windows", "Browser Windows", r"/browser-windows", "/browser-windows",
        componentes={
            "Nueva pestaña": "#tabButton", "Nueva ventana": "#windowButton",
            "Ventana con mensaje": "#messageWindowButton",
        },
    ),
    Pantalla(
        "alerts", "Alerts", r"/alerts", "/alerts",
        componentes={
            "Alert simple": "#alertButton", "Alert con demora": "#timerAlertButton",
            "Confirm": "#confirmButton",
            # Id real del sitio con error de tipeo: "promt" en vez de "prompt".
            "Prompt": "#promtButton",
        },
    ),
    Pantalla(
        "frames", "Frames", r"/frames", "/frames",
        componentes={"Frame 1": "#frame1", "Frame 2": "#frame2"},
    ),
    Pantalla("nestedframes", "Nested Frames", r"/nestedframes", "/nestedframes"),
    Pantalla(
        "modal-dialogs", "Modal Dialogs", r"/modal-dialogs", "/modal-dialogs",
        componentes={"Modal chico": "#showSmallModal", "Modal grande": "#showLargeModal"},
    ),
    # --- Widgets ---
    Pantalla(
        "accordian", "Accordian", r"/accordian", "/accordian",
        componentes={"Sección 1": "text=What is Lorem Ipsum?"},
    ),
    Pantalla(
        "auto-complete", "Auto Complete", r"/auto-complete", "/auto-complete",
        componentes={
            "Multiple colores": "#autoCompleteMultipleInput",
            "Un solo color": "#autoCompleteSingleInput",
        },
    ),
    Pantalla(
        "date-picker", "Date Picker", r"/date-picker", "/date-picker",
        componentes={
            "Fecha (mes/año)": "#datePickerMonthYearInput", "Fecha y hora": "#dateAndTimePickerInput",
        },
    ),
    Pantalla(
        "slider", "Slider", r"/slider", "/slider",
        componentes={"Control": "#slider", "Valor": "#sliderValue"},
    ),
    Pantalla(
        "progress-bar", "Progress Bar", r"/progress-bar", "/progress-bar",
        componentes={"Barra": "#progressBar", "Iniciar/Detener": "#startStopButton"},
    ),
    Pantalla(
        "tabs", "Tabs", r"/tabs", "/tabs",
        componentes={
            "Pestaña What": "#demo-tab-what", "Pestaña Origin": "#demo-tab-origin",
            "Pestaña Use": "#demo-tab-use",
        },
    ),
    Pantalla(
        "tool-tips", "Tool Tips", r"/tool-tips", "/tool-tips",
        # Varios ids del sitio tienen errores de tipeo ("toop"/"ToolTop" en vez de "tool"/"ToolTip").
        componentes={"Botón con tooltip": "#toolTipButton", "Campo con tooltip": "#toolTipTextField"},
    ),
    Pantalla(
        "menu", "Menu", r"/menu", "/menu",
        componentes={
            "Main Item 1": "text=Main Item 1", "Main Item 2": "text=Main Item 2",
            "Main Item 3": "text=Main Item 3",
        },
    ),
    Pantalla(
        "select-menu", "Select Menu", r"/select-menu", "/select-menu",
        componentes={
            "With Opt Group": "#withOptGroup", "Select One": "#selectOne",
            "Old Style Select Menu": "#oldSelectMenu", "Multiselect de autos": "#cars",
        },
    ),
    # --- Interactions ---
    Pantalla(
        "sortable", "Sortable", r"/sortable", "/sortable",
        componentes={"Elemento One": "text=One"},
    ),
    Pantalla(
        "selectable", "Selectable", r"/selectable", "/selectable",
        componentes={"Elemento Cras justo": "text=Cras justo odio"},
    ),
    Pantalla(
        "resizable", "Resizable", r"/resizable", "/resizable",
        componentes={"Con restricción": "#resizableBoxWithRestriction", "Sin restricción": "#resizable"},
    ),
    Pantalla(
        "droppable", "Droppable", r"/droppable", "/droppable",
        # Ojo: el id "droppable" se repite en más de una pestaña (simple y revertable);
        # escenario-ui debe ubicarlo dentro de la pestaña activa, no por id suelto.
        componentes={"Arrastrable": "#draggable", "Pestañas": "#droppableExample-tab-simple"},
    ),
    Pantalla(
        "dragabble", "Dragabble", r"/dragabble", "/dragabble",
        componentes={"Arrastrable": "#dragBox", "Pestañas": "#draggableExample-tab-simple"},
    ),
    # --- Book Store Application ---
    Pantalla(
        "bookstore-login", "Book Store: Login", r"/login", "/login",
        componentes={
            "Usuario": "#userName", "Contraseña": "#password", "Login": "#login",
            "Nuevo usuario": "#newUser",
        },
    ),
    Pantalla(
        "bookstore-register", "Book Store: Register", r"/register", "/register",
        componentes={
            "Nombre": "#firstname", "Apellido": "#lastname", "Usuario": "#userName",
            "Contraseña": "#password", "Registrarse": "#register",
        },
    ),
    Pantalla(
        "bookstore-books", "Book Store: catálogo", r"/books", "/books",
        componentes={"Buscar": "#searchBox", "Login": "#login"},
    ),
    Pantalla(
        "bookstore-profile", "Book Store: perfil", r"/profile", "/profile", requiere_sesion=True,
    ),
    Pantalla("bookstore-swagger", "Book Store API (Swagger)", r"/swagger", "/swagger"),
]

_POR_RUTA = [(re.compile(rf"^{p.ruta}/?$"), p) for p in PANTALLAS]


def pantalla_de_ruta(ruta: str) -> str:
    """'/text-box' -> 'Text Box'. Rutas desconocidas: la ruta misma."""
    for patron, pantalla in _POR_RUTA:
        if patron.match(ruta):
            return pantalla.nombre
    return ruta
