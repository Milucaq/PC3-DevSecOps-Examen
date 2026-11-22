import json
import os
from http.client import HTTPSConnection
from urllib.parse import urlsplit

from dotenv import load_dotenv

load_dotenv()


def obtener_puntos():
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        raise ValueError("Falta configurar Supabase")

    parsed = urlsplit(url)

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".supabase.co")
        or parsed.username
        or parsed.password
    ):
        raise ValueError("URL de Supabase no permitida")

    ruta = (
        "/rest/v1/puntos_demo"
        "?select=id,nombre,distrito,categoria"
        "&order=id.asc"
    )

    conexion = HTTPSConnection(
        parsed.hostname,
        timeout=15,
    )

    try:
        conexion.request(
            "GET",
            ruta,
            headers={
                "apikey": key,
                "Accept": "application/json",
            },
        )

        respuesta = conexion.getresponse()

        if respuesta.status != 200:
            raise RuntimeError(
                "Supabase devolvio un error HTTP"
            )

        datos = json.loads(
            respuesta.read().decode("utf-8")
        )

        if not isinstance(datos, list):
            raise TypeError("Respuesta inesperada")

        return datos

    finally:
        conexion.close()