"""Datos de Toolshop. Las credenciales se leen de variables de entorno.

Los valores por defecto son los usuarios de prueba públicos que publica el sitio
(https://github.com/testsmith-io/practice-software-testing).
"""

import os

API_URL = os.environ.get("TOOLSHOP_API_URL", "https://api.practicesoftwaretesting.com")

CLIENTE_EMAIL = os.environ.get("TOOLSHOP_CLIENTE_EMAIL", "customer@practicesoftwaretesting.com")
CLIENTE_CLAVE = os.environ.get("TOOLSHOP_CLIENTE_CLAVE", "welcome01")
