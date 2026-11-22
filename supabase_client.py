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
        
def guardar_embarcacion(datos):
    """Registra una embarcación usando credenciales del servidor."""

    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SECRET_KEY", "")

    if not url or not key:
        raise ValueError("Falta configurar acceso seguro a Supabase")

    parsed = urlsplit(url)

    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.endswith(".supabase.co")
        or parsed.username
        or parsed.password
        or parsed.port is not None
    ):
        raise ValueError("URL de Supabase no permitida")

    campos = {
        "nombre_embarcacion": datos["nombre_embarcacion"],
        "nombre_pescador": datos["nombre_pescador"],
        "llegada_estimada": datos["llegada_estimada"],
        "estado": datos["estado"],
    }

    conexion = HTTPSConnection(parsed.hostname, timeout=15)

    try:
        conexion.request(
            "POST",
            "/rest/v1/embarcaciones",
            body=json.dumps(campos, ensure_ascii=False),
            headers={
                "apikey": key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Prefer": "return=representation",
            },
        )

        respuesta = conexion.getresponse()
        contenido = respuesta.read()

        if respuesta.status != 201:
            raise RuntimeError(
                "No se pudo registrar la embarcación en Supabase"
            )

        registros = json.loads(contenido.decode("utf-8"))

        if not isinstance(registros, list) or len(registros) != 1:
            raise TypeError("Respuesta inesperada de Supabase")

        return registros[0]

    finally:
        conexion.close()