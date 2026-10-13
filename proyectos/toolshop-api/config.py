"""Datos de la API de Toolshop. Credenciales por variables de entorno.

Los valores por defecto son los usuarios de prueba públicos del sitio
(https://github.com/testsmith-io/practice-software-testing).
"""

import os

API_URL = os.environ.get("TOOLSHOP_API_URL", "https://api.practicesoftwaretesting.com")
TIMEOUT_S = float(os.environ.get("TOOLSHOP_API_TIMEOUT", "30"))
UMBRAL_RESPUESTA_S = float(os.environ.get("TOOLSHOP_API_UMBRAL", "5"))

CLIENTE_EMAIL = os.environ.get("TOOLSHOP_CLIENTE_EMAIL", "customer@practicesoftwaretesting.com")
CLIENTE_CLAVE = os.environ.get("TOOLSHOP_CLIENTE_CLAVE", "welcome01")
