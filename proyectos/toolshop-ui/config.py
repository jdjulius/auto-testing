"""Datos de Toolshop para las pruebas de UI. Credenciales por variables de entorno.

Los valores por defecto son los usuarios de prueba públicos del sitio
(https://github.com/testsmith-io/practice-software-testing).
"""

import os

CLIENTE_EMAIL = os.environ.get("TOOLSHOP_CLIENTE_EMAIL", "customer@practicesoftwaretesting.com")
CLIENTE_CLAVE = os.environ.get("TOOLSHOP_CLIENTE_CLAVE", "welcome01")
