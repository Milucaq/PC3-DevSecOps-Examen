import json
import os
from urllib.request import Request, urlopen

from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL", "").rstrip("/")
key = os.getenv("SUPABASE_KEY", "")

if not url or not key:
    raise RuntimeError(
        "Faltan SUPABASE_URL o SUPABASE_KEY en .env"
    )

endpoint = (
    f"{url}/rest/v1/puntos_demo"
    "?select=id,nombre,distrito,categoria"
    "&order=id.asc"
)

request = Request(
    endpoint,
    headers={
        "apikey": key,
        "Accept": "application/json",
    },
)

try:
    with urlopen(request, timeout=15) as response:
        registros = json.load(response)

    print("Conexion con Supabase exitosa")
    print(json.dumps(registros, indent=2, ensure_ascii=False))

except Exception as error:
    print(f"Error de conexion: {type(error).__name__}")
    raise