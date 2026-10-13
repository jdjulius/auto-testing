---
name: escenario-api
description: Escribir pruebas de API REST con pytest + httpx en los proyectos proyectos/*-api de este monorepo (cliente con evidencias en Allure, esquemas JSON, autenticación por token, casos positivos, negativos y de permisos). Úsala siempre que pidan probar un endpoint, agregar pruebas de API, validar respuestas o esquemas, probar autenticación o permisos, o convertir en prueba una llamada que hace la UI — aunque no digan "API".
---

# Escenarios de API (pytest + httpx)

Proyecto de referencia: `proyectos/toolshop-api/`. No usa navegador
(`-p no:playwright` en su `pytest.ini`).

```
cliente/api.py        ClienteApi (httpx): URL base, token, evidencias en Allure, enmascarado
esquemas/*.json       JSON Schema por recurso (se referencian entre sí: "$ref": "producto.json")
config.py             URL y credenciales por variables de entorno
tests/api/conftest.py fixtures
tests/api/test_<recurso>.py
```

## 1. Antes de escribir

- Mira la especificación (OpenAPI/Swagger) y **una respuesta real** del endpoint;
  los esquemas y aserciones salen de ahí. Toolshop publica la suya en
  `https://api.practicesoftwaretesting.com/docs?api-docs.json`.
- Si el endpoint lo consume la UI, revisa cómo lo llama (método, cuerpo, headers):
  Toolshop, por ejemplo, usa el método HTTP `QUERY` para listar y filtrar (`api.query(...)`).

## 2. Fixtures disponibles (toolshop-api)

| Fixture | Qué da | Alcance |
|---|---|---|
| `api` | Cliente anónimo | sesión |
| `token` | Token del usuario cliente (login una vez) | sesión |
| `api_cliente` | Cliente autenticado (`Authorization: Bearer`) | sesión |
| `producto` | Un producto real del catálogo (no fijar ids ni nombres) | sesión |
| `carrito` | Carrito nuevo que se **borra al terminar** | prueba |

Toda prueba que crea datos los limpia en un fixture con `yield`: el ambiente se
comparte y no debe quedar basura.

## 3. Cómo escribir la prueba

```python
@pytest.mark.escenario(
    modulo="Carrito",
    funcionalidad="Validaciones",
    descripcion="Rechazar cantidades menores a 1",
    resultado_esperado="422 con el error del campo quantity",
    prioridad="Alta",
)
@pytest.mark.parametrize("cantidad", [0, -1], ids=["cero", "negativa"])
def test_cantidad_invalida(api, carrito, producto, cantidad):
    respuesta = api.post(f"/carts/{carrito}", json={"product_id": producto["id"], "quantity": cantidad})
    assert respuesta.status_code == 422
    assert "quantity" in respuesta.json().get("errors", {})
```

- Usa siempre el cliente (`api.get/post/put/delete/query`), nunca `httpx` directo:
  así cada llamada queda como paso en Allure con request y response enmascarados.
- Verifica **status y contenido**: `validar_esquema(datos, "producto")` y además los
  valores que importan (mismo id que se pidió, total coherente, etc.).
- Mensajes de error con contexto: `assert r.status_code == 200, r.text`.

## 4. Qué casos cubrir por endpoint

| Tipo | Ejemplos |
|---|---|
| Caso feliz | 200/201 + esquema + valores |
| Validación | cada campo obligatorio, tipos y formatos inválidos, límites → 400/422 con el campo en `errors` |
| Inexistente | id que no existe → 404 con esquema `error` |
| Autenticación | sin token, token inválido o vencido → 401 |
| Autorización | rol sin permiso (cliente contra endpoint de admin) → 403 |
| Consistencia | lo creado se puede leer; lo borrado da 404; paginación sin repetidos |
| Datos sensibles | la respuesta no expone `password` ni tokens (el esquema `usuario` lo verifica con `not required password`) |
| Tiempo | responde bajo `config.UMBRAL_RESPUESTA_S` |

## 5. Esquemas

- Uno por recurso en `esquemas/`. Exige los campos esenciales con su tipo y deja
  pasar campos adicionales: la API puede crecer sin romper las pruebas, pero se
  detecta si falta o cambia de tipo algo que se usa.
- Reutiliza con `$ref` (`pagina_productos.json` → `producto.json`); `validar_esquema`
  carga todos los archivos en un registro y muestra todos los errores juntos.

## 6. Reglas

- Credenciales solo por variables de entorno (`config.py`); en CI, como secrets.
- No dependas de datos que otros pueden cambiar: tómalos de la propia API
  (fixture `producto`) o créalos y bórralos en la prueba.
- Si un endpoint tiene un defecto real, `xfail(strict=True, reason=...)` con la
  expectativa correcta (skill `levantar-escenarios`).
- Antes de terminar: `pytest --collect-only -q` (IDs nuevos) y `pytest` completo.
