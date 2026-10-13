import re

import allure
from playwright.sync_api import Page, expect


def precio(texto: str) -> float:
    return float(re.search(r"[\d.]+", texto.replace(",", "")).group())


class CatalogoPage:
    """Home y páginas de categoría: tarjetas de producto, búsqueda, orden y filtros."""

    def __init__(self, page: Page) -> None:
        self.page = page
        self.nombres = page.get_by_test_id("product-name")
        self.precios = page.get_by_test_id("product-price")
        self.buscador = page.get_by_test_id("search-query")
        self.boton_buscar = page.get_by_test_id("search-submit")
        self.termino_buscado = page.get_by_test_id("search-term")
        self.orden = page.get_by_test_id("sort")
        self.titulo = page.get_by_test_id("page-title")

    @allure.step("Abrir el catálogo")
    def abrir(self, ruta: str = "/") -> "CatalogoPage":
        self.page.goto(ruta)
        self.esperar_productos()
        return self

    def esperar_productos(self) -> None:
        expect(self.nombres.first).to_be_visible()

    def lista_nombres(self) -> list[str]:
        return [n.strip() for n in self.nombres.all_inner_texts()]

    def lista_precios(self) -> list[float]:
        return [precio(p) for p in self.precios.all_inner_texts()]

    @allure.step("Buscar '{termino}'")
    def buscar(self, termino: str) -> None:
        self.buscador.fill(termino)
        self.boton_buscar.click()
        expect(self.termino_buscado).to_have_text(termino)

    @allure.step("Ordenar por '{valor}'")
    def ordenar(self, valor: str) -> None:
        # La UI marca el fin del ordenamiento con data-test="sorting_completed".
        self.orden.select_option(valor)
        expect(self.page.get_by_test_id("sorting_completed")).to_be_attached()

    @allure.step("Abrir el producto {indice}")
    def abrir_producto(self, indice: int = 0) -> tuple[str, float]:
        nombre = self.nombres.nth(indice).inner_text().strip()
        valor = precio(self.precios.nth(indice).inner_text())
        self.nombres.nth(indice).click()
        return nombre, valor
