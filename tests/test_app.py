import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_pagina_principal(client):
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert b"PescaConecta" in respuesta.data


def test_api_health(client):
    respuesta = client.get("/api/health")

    assert respuesta.status_code == 200

    datos = respuesta.get_json()
    assert datos["status"] == "ok"
    assert datos["message"] == "API Flask funcionando"


def test_ruta_inexistente(client):
    respuesta = client.get("/ruta-inexistente")

    assert respuesta.status_code == 404
def test_api_puntos(client, monkeypatch):
    def puntos_simulados():
        return [
            {
                "id": 1,
                "nombre": "Punto de prueba",
                "distrito": "Comas",
                "categoria": "Reciclaje",
            }
        ]

    monkeypatch.setattr(
        "app.obtener_puntos",
        puntos_simulados,
    )

    respuesta = client.get("/api/puntos")

    assert respuesta.status_code == 200

    datos = respuesta.get_json()

    assert datos["status"] == "ok"
    assert datos["total"] == 1
    assert len(datos["datos"]) == 1


def test_api_puntos_error(client, monkeypatch):
    def consulta_fallida():
        raise ValueError("Error simulado")

    monkeypatch.setattr(
        "app.obtener_puntos",
        consulta_fallida,
    )

    respuesta = client.get("/api/puntos")

    assert respuesta.status_code == 503

    datos = respuesta.get_json()

    assert datos["status"] == "error"
    assert datos["message"] == (
        "No se pudieron consultar los puntos"
    )
    
 # HU-03 (PC3EX-8): pruebas del registro de embarcaciones

@pytest.fixture
def embarcacion_valida():
    return {
        "nombre_embarcacion": "Mar Azul",
        "nombre_pescador": "Juan Perez",
        "llegada_estimada": "2026-11-22T10:30:00-05:00",
        "estado": "Regresando",
    }


@pytest.mark.parametrize("contenido", [
    None,
    [],
    "texto",
])
def test_registro_rechaza_json_invalido(client, contenido):
    respuesta = client.post(
        "/api/embarcaciones",
        json=contenido,
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["status"] == "error"


@pytest.mark.parametrize("campo,valor", [
    ("nombre_embarcacion", None),
    ("nombre_pescador", 123),
    ("llegada_estimada", None),
    ("estado", 999),
])
def test_registro_rechaza_tipos_invalidos(
    client, embarcacion_valida, campo, valor
):
    datos = embarcacion_valida.copy()
    datos[campo] = valor

    respuesta = client.post(
        "/api/embarcaciones",
        json=datos,
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["status"] == "error"


@pytest.mark.parametrize("campo,valor", [
    ("nombre_embarcacion", "A"),
    ("nombre_embarcacion", "A" * 121),
    ("nombre_pescador", " "),
    ("nombre_pescador", "B" * 121),
])
def test_registro_rechaza_nombres_invalidos(
    client, embarcacion_valida, campo, valor
):
    datos = embarcacion_valida.copy()
    datos[campo] = valor

    respuesta = client.post(
        "/api/embarcaciones",
        json=datos,
    )

    assert respuesta.status_code == 400


def test_registro_rechaza_estado_invalido(
    client, embarcacion_valida
):
    datos = embarcacion_valida.copy()
    datos["estado"] = "Volando"

    respuesta = client.post(
        "/api/embarcaciones",
        json=datos,
    )

    assert respuesta.status_code == 400
    assert "Estado" in respuesta.get_json()["message"]


@pytest.mark.parametrize("fecha", [
    "fecha-invalida",
    "2026-11-22T10:30:00",
])
def test_registro_rechaza_fecha_invalida(
    client, embarcacion_valida, fecha
):
    datos = embarcacion_valida.copy()
    datos["llegada_estimada"] = fecha

    respuesta = client.post(
        "/api/embarcaciones",
        json=datos,
    )

    assert respuesta.status_code == 400
    assert "zona horaria" in respuesta.get_json()["message"]


def test_registro_valido(client, embarcacion_valida, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")

    def guardar_simulado(datos):
        return {"id": "demo-001", **datos}

    monkeypatch.setattr(
        "app.guardar_embarcacion",
        guardar_simulado,
    )

    respuesta = client.post(
        "/api/embarcaciones",
        json=embarcacion_valida,
        headers={"X-Admin-Token": "token-prueba"},
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["status"] == "ok"


def test_registro_estado_por_defecto(
    client, embarcacion_valida, monkeypatch
):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")

    def guardar_simulado(datos):
        return datos

    monkeypatch.setattr(
        "app.guardar_embarcacion",
        guardar_simulado,
    )

    datos = embarcacion_valida.copy()
    datos.pop("estado")

    respuesta = client.post(
        "/api/embarcaciones",
        json=datos,
        headers={"X-Admin-Token": "token-prueba"},
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["estado"] == "En faena"
def test_portal_pescador(client):
    respuesta = client.get("/pescador")

    assert respuesta.status_code == 200
    assert b"formEmbarcacion" in respuesta.data
# Sprint 2 - Catalogo pesquero


def test_catalogo_productos(client, monkeypatch):
    monkeypatch.setattr(
        "app.consultar_productos",
        lambda: [{"especie": "Bonito", "cantidad_kg": 50}],
    )
    respuesta = client.get("/api/productos")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["total"] == 1


def test_catalogo_error(client, monkeypatch):
    def fallo():
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.consultar_productos", fallo)
    assert client.get("/api/productos").status_code == 503


def test_publicar_producto(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")
    monkeypatch.setattr(
        "app.guardar_producto",
        lambda datos: {"id": "demo", **datos},
    )

    respuesta = client.post(
        "/api/productos",
        json={"especie": "Bonito", "cantidad_kg": 50, "precio_kg": 9.5},
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["especie"] == "Bonito"


def test_publicar_sin_autorizacion(client):
    respuesta = client.post(
        "/api/productos",
        json={"especie": "Bonito", "cantidad_kg": 50, "precio_kg": 9.5},
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("datos", [
    None,
    {"especie": "A", "cantidad_kg": 50, "precio_kg": 9},
    {"especie": 123, "cantidad_kg": 50, "precio_kg": 9},
    {"especie": "Bonito", "cantidad_kg": "50", "precio_kg": 9},
    {"especie": "Bonito", "cantidad_kg": 50, "precio_kg": True},
    {"especie": "Bonito", "cantidad_kg": -5, "precio_kg": 9},
])
def test_publicacion_invalida(client, monkeypatch, datos):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")
    respuesta = client.post(
        "/api/productos",
        json=datos,
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 400


def test_publicacion_error_supabase(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")

    def fallo(datos):
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.guardar_producto", fallo)

    respuesta = client.post(
        "/api/productos",
        json={"especie": "Bonito", "cantidad_kg": 50, "precio_kg": 9.5},
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 503
# PC3EX-9 - Actualizar estado de desembarque

ID_EMBARCACION = "123e4567-e89b-42d3-a456-426614174000"


def test_actualizar_desembarque(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")
    monkeypatch.setattr(
        "app.actualizar_estado_embarcacion",
        lambda identificador, estado: {
            "id": identificador,
            "estado": estado,
        },
    )

    respuesta = client.patch(
        f"/api/embarcaciones/{ID_EMBARCACION}/estado",
        json={"estado": "Arribó"},
        headers={"X-Admin-Token": "token-prueba"},
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["estado"] == "Arribó"


def test_actualizar_desembarque_sin_token(client):
    respuesta = client.patch(
        f"/api/embarcaciones/{ID_EMBARCACION}/estado",
        json={"estado": "Arribó"},
    )
    assert respuesta.status_code == 403


def test_actualizar_desembarque_id_invalido(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")
    respuesta = client.patch(
        "/api/embarcaciones/invalido/estado",
        json={"estado": "Arribó"},
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 400


def test_actualizar_desembarque_estado_invalido(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")
    respuesta = client.patch(
        f"/api/embarcaciones/{ID_EMBARCACION}/estado",
        json={"estado": "Desconocido"},
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 400


def test_actualizar_desembarque_no_encontrado(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")

    def no_encontrado(identificador, estado):
        raise LookupError("No encontrado")

    monkeypatch.setattr("app.actualizar_estado_embarcacion", no_encontrado)

    respuesta = client.patch(
        f"/api/embarcaciones/{ID_EMBARCACION}/estado",
        json={"estado": "Arribó"},
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 404


def test_actualizar_desembarque_error(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")

    def fallo(identificador, estado):
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.actualizar_estado_embarcacion", fallo)

    respuesta = client.patch(
        f"/api/embarcaciones/{ID_EMBARCACION}/estado",
        json={"estado": "Arribó"},
        headers={"X-Admin-Token": "token-prueba"},
    )
    assert respuesta.status_code == 503