---
name: escenario-ui
description: Escribir o corregir pruebas de interfaz con pytest + Playwright en los proyectos proyectos/*-ui de este monorepo (Page Objects, selectores data-test, esperas, fixtures, defectos conocidos). Úsala siempre que pidan automatizar una pantalla o un flujo web, agregar pruebas de UI, arreglar una prueba de UI que falla o que pasa a veces, o crear Page Objects — aunque no mencionen Playwright.
---

# Escenarios de UI (pytest + Playwright)

Proyectos: `proyectos/saucedemo-ui/`, `proyectos/toolshop-ui/` (y los que se agreguen).
Cada uno tiene `pages/` (Page Objects), `pages/mapa.py` (mapa de pantallas),
`tests/ui/` y `tests/ui/conftest.py` (fixtures).

## 1. Antes de escribir: mira la app de verdad

No adivines selectores ni textos esperados. Abre la pantalla y anota componentes,
textos y comportamiento real (skill `relevar-pantallas`, script
`.claude/skills/relevar-pantallas/scripts/explorar.py`). Los resultados esperados se
derivan de la app y de la regla de negocio, nunca de lo que "debería" decir.

## 2. Estructura

- **Page Object por pantalla** en `pages/<pantalla>.py`: guarda los locators en
  `__init__` y expone acciones (`ingresar`, `agregar`, `completar_datos`). Si un
  selector cambia, se corrige en un solo lugar.
- Decora las acciones con `@allure.step("Agregar al carrito: {nombre}")`: aparecen
  como pasos en Allure. Nunca pongas contraseñas en el texto del paso.
- **Fixtures** en `tests/ui/conftest.py` para el estado inicial (`login`,
  `inventario` en saucedemo; `catalogo`, `sesion` en toolshop). La prueba solo
  contiene lo propio del escenario.
- Credenciales y datos en `config.py`, leídos de variables de entorno con un valor
  por defecto solo si es un usuario de prueba público.

## 3. Selectores (en este orden)

1. Atributo de prueba: `page.get_by_test_id("login-button")`. Ambos sitios usan
   `data-test`, configurado en `tests/ui/conftest.py` con
   `playwright.selectors.set_test_id_attribute("data-test")`.
2. Rol y texto visible: `get_by_role("button", name="Add to cart")`.
3. Etiqueta: `get_by_label("Username")`.
4. `id` estable; CSS/XPath por estructura solo como último recurso.

Si un enlace cambia de texto (Twitter pasó a llamarse "X"), prefiere el rol con el
nombre visible actual o el atributo de prueba.

## 4. Esperas: la causa número uno de pruebas inestables

- Usa `expect(...)` (espera sola) en vez de leer valores inmediatamente.
  `locator.count()`, `inner_text()` y `all_inner_texts()` **no esperan**.
- **En apps SPA la URL cambia antes de que se dibuje la pantalla nueva.** Después de
  navegar, espera un componente **propio** de la pantalla destino antes de leer datos:

  ```python
  page.get_by_test_id("item-4-title-link").click()
  expect(page).to_have_url(re.compile(r"/inventory-item\.html\?id=4$"))
  expect(page.get_by_test_id("back-to-products")).to_be_visible()   # solo existe en el detalle
  expect(page.get_by_test_id("inventory-item-name")).to_have_text("Sauce Labs Backpack")
  ```

- Para listas que cambian (ordenar, filtrar) espera la señal que dé la app
  (`sorting_completed` en Toolshop) o el primer elemento, no un `wait_for_timeout`.
- Nunca uses `time.sleep` ni `wait_for_timeout` para "dar tiempo": si hace falta,
  falta una espera explícita.

## 5. Verificaciones

- Compara contra la regla, no contra datos fijos que pueden cambiar. En sitios
  compartidos (Toolshop) los productos los editan otros usuarios: compara la tarjeta
  contra el detalle, o contra la API, en vez de fijar nombres o precios.
- Una prueba, un comportamiento; varias aserciones del mismo comportamiento están bien.
- Para pantallas con muchos componentes, junta los faltantes y falla una vez con la
  lista completa (ver `tests/ui/test_pantallas.py`).
- Variantes con `@pytest.mark.parametrize(..., ids=[...])`.

## 6. Escenario

Cada prueba lleva `@pytest.mark.escenario(...)` (skill `levantar-escenarios`):
módulo, funcionalidad, descripción, resultado esperado verificable y prioridad.

## 7. Antes de dar la prueba por buena

1. `pytest --collect-only -q` → revisa el ID nuevo.
2. Ejecuta la prueba **3 veces seguidas** (`for i in 1 2 3; do pytest -k <nombre> --sin-registro; done`):
   una prueba que pasa 2 de 3 tiene una espera mal hecha, no un defecto de la app.
3. Si falla, mira la causa real (traza, captura en `test-results/`, `--headed --slowmo 500`)
   antes de concluir que es un defecto. Si lo es, márcalo como `xfail(strict=True)`.
4. Ejecuta el archivo completo o el proyecto para no romper otras pruebas.
