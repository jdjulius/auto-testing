---
name: relevar-pantallas
description: Relevar (explorar en vivo) las pantallas de una aplicación web para levantar escenarios — rutas, componentes con atributo de prueba, textos, APIs que llama cada pantalla y comportamientos o defectos no evidentes — y registrarlas en pages/mapa.py con su prueba de pantallas. Úsala al empezar a probar una aplicación o pantalla nueva, cuando pidan mapear pantallas o componentes, buscar más escenarios o defectos, o cuando no se sepa qué selector o texto usar.
---

# Relevar pantallas

El objetivo es que los escenarios salgan de **lo que la app hace de verdad**, no de
suposiciones. Todo lo que encuentres se convierte en: una entrada del mapa de
pantallas, un escenario nuevo o un defecto conocido.

## 1. Explorar con el script

```bash
python .claude/skills/relevar-pantallas/scripts/explorar.py https://practicesoftwaretesting.com \
    / /auth/login /contact --api-host api.practicesoftwaretesting.com
# con sesión iniciada antes de recorrer:
python .claude/skills/relevar-pantallas/scripts/explorar.py https://practicesoftwaretesting.com /account \
    --login /auth/login --usuario customer@practicesoftwaretesting.com --clave welcome01
```

Por cada ruta muestra la URL final, el título, los valores visibles del atributo
de prueba (`--atributo data-testid` si el sitio usa otro) y las llamadas a la API
(método, status, URL). Solo navega y lee: no modifica datos.

Para flujos con varios pasos (carrito → checkout), escribe un script corto de
Playwright que haga los pasos e imprima lo mismo en cada uno; el script es la base.
`python -m playwright codegen <url>` también ayuda a ver selectores.

## 2. Qué anotar por pantalla

- Ruta (y su forma con parámetros: `/product/{id}`), título y componentes con su selector.
- Diferencias **con y sin sesión**: la misma pantalla cambia (en Toolshop, el
  contacto con sesión ya no pide nombre ni email).
- APIs que llama al cargar y en cada acción: método, ruta, cuerpo. El método puede
  ser poco común (`QUERY` en Toolshop) y los cuerpos pueden llevar contraseñas:
  enmascáralas en cualquier nota que guardes.
- Datos que cambian solos: en sitios compartidos otros usuarios editan productos;
  no los uses como valores fijos.

## 3. Buscar comportamientos no evidentes

Con un script de Playwright revisa lo que no se ve a simple vista; así salieron
varios defectos reales de saucedemo:

- cookies y `localStorage` (¿una cookie forjada da acceso?, ¿el carrito persiste?);
- códigos HTTP de las rutas (`page.goto(ruta).status`);
- validaciones con datos límite (vacío, solo espacios, acentos, scripts);
- reglas de negocio (¿se puede comprar con el carrito vacío?);
- ids inexistentes, botón Atrás tras cerrar sesión, errores de JavaScript (`page.on("pageerror")`);
- tamaños de pantalla (móvil, tablet) y cada tipo de usuario o rol.

Confirma cada hallazgo con una espera adecuada antes de llamarlo defecto: varias
"fallas" eran lecturas hechas antes de que la pantalla terminara de dibujarse.

## 4. Registrar en el mapa de pantallas

En `pages/mapa.py` del proyecto, una entrada `Pantalla` por pantalla: clave, nombre,
ruta (en toolshop-ui, expresión regular; ver `pantalla_de_ruta`), ejemplo para
abrirla, título opcional, componentes `{nombre legible: data-test}` y si requiere
sesión. `tests/ui/test_pantallas.py` genera un escenario por pantalla que verifica
ruta, título y todos los componentes, y lista juntos los que falten.

Incluye solo componentes que viste visibles: un contenedor que existe pero no se
dibuja (como `filters` en Toolshop) hace fallar la prueba sin que haya defecto.

## 5. Convertir el relevamiento en escenarios

- Comportamiento correcto → escenario normal (skills `escenario-ui` / `escenario-api`).
- Defecto → escenario con la expectativa correcta y `xfail(strict=True, reason=...)`.
- APIs observadas → candidatas a pruebas de API en el proyecto `*-api`.
- Levanta con `pytest --collect-only -q` y revisa los IDs nuevos.
