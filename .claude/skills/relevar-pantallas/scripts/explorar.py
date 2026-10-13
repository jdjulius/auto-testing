"""Explora pantallas de una aplicación web: componentes con atributo de prueba y APIs que llama.

Uso (desde cualquier carpeta, con Playwright instalado):

    python explorar.py https://mi-app.com / /login /productos
    python explorar.py https://mi-app.com / --atributo data-testid --api-host api.mi-app.com
    python explorar.py https://mi-app.com /account --login /auth/login --usuario u@x.com --clave secreta \
        --campo-usuario email --campo-clave password --boton login-submit

Por cada ruta imprime:
  - la URL final y el título;
  - los valores del atributo de prueba (data-test por defecto) visibles en la pantalla;
  - las llamadas xhr/fetch que hizo la página (método, URL, status).

No modifica nada en la aplicación: solo navega y lee. Si se indica --login, inicia
sesión una vez antes de recorrer las rutas.
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("base_url")
    p.add_argument("rutas", nargs="+", help="rutas relativas a base_url, por ejemplo / /login")
    p.add_argument("--atributo", default="data-test", help="atributo de prueba (data-test, data-testid, data-cy…)")
    p.add_argument("--api-host", action="append", default=[], help="host de la API propia (se puede repetir)")
    p.add_argument("--espera-ms", type=int, default=1500, help="espera extra tras cargar cada ruta")
    p.add_argument("--login", help="ruta de login para iniciar sesión antes de recorrer")
    p.add_argument("--usuario")
    p.add_argument("--clave")
    p.add_argument("--campo-usuario", default="email", help="valor del atributo de prueba del campo usuario")
    p.add_argument("--campo-clave", default="password")
    p.add_argument("--boton", default="login-submit")
    p.add_argument("--headed", action="store_true", help="ver el navegador")
    a = p.parse_args(argv)

    with sync_playwright() as pw:
        pw.selectors.set_test_id_attribute(a.atributo)
        navegador = pw.chromium.launch(headless=not a.headed)
        pagina = navegador.new_context().new_page()
        llamadas: list[list] = []

        def al_salir(request):
            if request.resource_type in ("xhr", "fetch"):
                try:
                    pantalla = urlsplit(request.frame.url).path
                except Exception:
                    pantalla = ""
                llamadas.append([pantalla, request.method, request.url, None, request])

        def al_terminar(request):
            for fila in llamadas:
                if fila[4] is request:
                    try:
                        fila[3] = request.response().status
                    except Exception:
                        fila[3] = "?"

        pagina.on("request", al_salir)
        pagina.on("requestfinished", al_terminar)

        if a.login:
            pagina.goto(urljoin(a.base_url, a.login))
            pagina.get_by_test_id(a.campo_usuario).fill(a.usuario or "")
            pagina.get_by_test_id(a.campo_clave).fill(a.clave or "")
            pagina.get_by_test_id(a.boton).click()
            pagina.wait_for_load_state("networkidle")
            print(f"Sesión iniciada: {pagina.url}\n")
            llamadas.clear()

        for ruta in a.rutas:
            pagina.goto(urljoin(a.base_url, ruta))
            pagina.wait_for_load_state("networkidle")
            pagina.wait_for_timeout(a.espera_ms)
            valores = pagina.eval_on_selector_all(
                f"[{a.atributo}]",
                "(els, attr) => els.filter(e => e.getClientRects().length > 0).map(e => e.getAttribute(attr))",
                a.atributo,
            )
            print(f"== {ruta}  ->  {pagina.url}")
            print(f"   título: {pagina.title()!r}")
            print(f"   {a.atributo} visibles ({len(set(valores))}):")
            for valor in sorted(set(v for v in valores if v)):
                print(f"     - {valor}  (x{valores.count(valor)})" if valores.count(valor) > 1 else f"     - {valor}")
            propias = [ll for ll in llamadas if not a.api_host or urlsplit(ll[2]).netloc in a.api_host]
            print(f"   APIs llamadas ({len(propias)}):")
            for _, metodo, url, status, _ in propias:
                print(f"     {metodo:6} {status!s:4} {url[:120]}")
            print()
            llamadas.clear()
        navegador.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
