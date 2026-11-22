import pytest

from app import app

PRODUCTO_ID = "123e4567-e89b-42d3-a456-426614174000"
RESERVA_ID = "123e4567-e89b-42d3-a456-426614174001"

PRODUCTO = {
    "id": PRODUCTO_ID,
    "especie": "Bonito Demo",
    "cantidad_kg": 50,
    "precio_kg": 9.5,
    "disponible": True,
}


@pytest.fixture
def client(monkeypatch):
    app.config["TESTING"] = True
    monkeypatch.setenv("PESCACONECTA_ADMIN_TOKEN", "token-prueba")
    monkeypatch.delenv("PESCACONECTA_DEMO_RESERVAS", raising=False)

    with app.test_client() as cliente:
        yield cliente


def headers():
    return {"X-Admin-Token": "token-prueba"}


def reserva_valida():
    return {
        "producto_id": PRODUCTO_ID,
        "nombre_comprador": "Comprador Demo",
        "cantidad_kg": 5,
    }


def simular_producto(monkeypatch, producto=None):
    monkeypatch.setattr(
        "app.consultar_producto_detalle",
        lambda identificador: PRODUCTO if producto is None else producto,
    )


# HU-07: Detalle del producto


def test_detalle_producto(client, monkeypatch):
    simular_producto(monkeypatch)
    respuesta = client.get(f"/api/productos/{PRODUCTO_ID}")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["especie"] == "Bonito Demo"


def test_detalle_id_invalido(client):
    respuesta = client.get("/api/productos/invalido")
    assert respuesta.status_code == 400


def test_detalle_no_encontrado(client, monkeypatch):
    def fallo(identificador):
        raise LookupError("No encontrado")

    monkeypatch.setattr("app.consultar_producto_detalle", fallo)
    respuesta = client.get(f"/api/productos/{PRODUCTO_ID}")

    assert respuesta.status_code == 404


def test_detalle_error_servidor(client, monkeypatch):
    def fallo(identificador):
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.consultar_producto_detalle", fallo)
    respuesta = client.get(f"/api/productos/{PRODUCTO_ID}")

    assert respuesta.status_code == 503


# HU-08: Solicitar reserva


def test_reserva_exitosa(client, monkeypatch):
    simular_producto(monkeypatch)
    monkeypatch.setattr(
        "app.guardar_reserva",
        lambda datos: {"id": RESERVA_ID, **datos},
    )

    respuesta = client.post(
        "/api/reservas",
        json=reserva_valida(),
        headers=headers(),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["estado"] == "Pendiente"


def test_reserva_sin_autorizacion(client):
    respuesta = client.post(
        "/api/reservas",
        json=reserva_valida(),
    )
    assert respuesta.status_code == 403


@pytest.mark.parametrize("datos", [
    None,
    {},
    {"producto_id": "invalido", "nombre_comprador": "Ana", "cantidad_kg": 2},
    {"producto_id": PRODUCTO_ID, "nombre_comprador": "A", "cantidad_kg": 2},
    {"producto_id": PRODUCTO_ID, "nombre_comprador": "Ana", "cantidad_kg": 0},
    {"producto_id": PRODUCTO_ID, "nombre_comprador": "Ana", "cantidad_kg": -1},
    {"producto_id": PRODUCTO_ID, "nombre_comprador": "Ana", "cantidad_kg": True},
])
def test_reserva_datos_invalidos(client, datos):
    respuesta = client.post(
        "/api/reservas",
        json=datos,
        headers=headers(),
    )
    assert respuesta.status_code == 400


def test_reserva_cantidad_insuficiente(client, monkeypatch):
    simular_producto(monkeypatch)

    datos = reserva_valida()
    datos["cantidad_kg"] = 100

    respuesta = client.post(
        "/api/reservas",
        json=datos,
        headers=headers(),
    )

    assert respuesta.status_code == 409


def test_reserva_producto_no_disponible(client, monkeypatch):
    simular_producto(monkeypatch, {**PRODUCTO, "disponible": False})

    respuesta = client.post(
        "/api/reservas",
        json=reserva_valida(),
        headers=headers(),
    )
    assert respuesta.status_code == 409


def test_reserva_producto_no_encontrado(client, monkeypatch):
    def fallo(identificador):
        raise LookupError("No encontrado")

    monkeypatch.setattr("app.consultar_producto_detalle", fallo)

    respuesta = client.post(
        "/api/reservas",
        json=reserva_valida(),
        headers=headers(),
    )
    assert respuesta.status_code == 404


def test_reserva_error_supabase(client, monkeypatch):
    simular_producto(monkeypatch)

    def fallo(datos):
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.guardar_reserva", fallo)

    respuesta = client.post(
        "/api/reservas",
        json=reserva_valida(),
        headers=headers(),
    )
    assert respuesta.status_code == 503


def test_reserva_modo_demo_local(client, monkeypatch):
    monkeypatch.setenv("PESCACONECTA_DEMO_RESERVAS", "1")
    simular_producto(monkeypatch)
    monkeypatch.setattr(
        "app.guardar_reserva",
        lambda datos: {"id": RESERVA_ID, **datos},
    )

    respuesta = client.post(
        "/api/reservas",
        json=reserva_valida(),
    )
    assert respuesta.status_code == 201


# HU-09: Confirmar y rechazar reservas


@pytest.mark.parametrize("estado", ["Confirmada", "Rechazada"])
def test_actualizar_reserva(client, monkeypatch, estado):
    monkeypatch.setattr(
        "app.cambiar_estado_reserva",
        lambda identificador, nuevo: {
            "id": identificador,
            "estado": nuevo,
        },
    )

    respuesta = client.patch(
        f"/api/reservas/{RESERVA_ID}/estado",
        json={"estado": estado},
        headers=headers(),
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["estado"] == estado


def test_actualizar_reserva_sin_token(client):
    respuesta = client.patch(
        f"/api/reservas/{RESERVA_ID}/estado",
        json={"estado": "Confirmada"},
    )
    assert respuesta.status_code == 403


def test_actualizar_reserva_id_invalido(client):
    respuesta = client.patch(
        "/api/reservas/invalido/estado",
        json={"estado": "Confirmada"},
        headers=headers(),
    )
    assert respuesta.status_code == 400


def test_actualizar_reserva_estado_invalido(client):
    respuesta = client.patch(
        f"/api/reservas/{RESERVA_ID}/estado",
        json={"estado": "Pendiente"},
        headers=headers(),
    )
    assert respuesta.status_code == 400


def test_actualizar_reserva_no_encontrada(client, monkeypatch):
    def fallo(identificador, estado):
        raise LookupError("No encontrada")

    monkeypatch.setattr("app.cambiar_estado_reserva", fallo)

    respuesta = client.patch(
        f"/api/reservas/{RESERVA_ID}/estado",
        json={"estado": "Confirmada"},
        headers=headers(),
    )
    assert respuesta.status_code == 404


def test_actualizar_reserva_error(client, monkeypatch):
    def fallo(identificador, estado):
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.cambiar_estado_reserva", fallo)

    respuesta = client.patch(
        f"/api/reservas/{RESERVA_ID}/estado",
        json={"estado": "Confirmada"},
        headers=headers(),
    )
    assert respuesta.status_code == 503


# Panel administrativo


def test_pagina_reservas(client):
    respuesta = client.get("/reservas")
    assert respuesta.status_code == 200
    assert b"formReserva" in respuesta.data


def test_listar_reservas(client, monkeypatch):
    monkeypatch.setattr(
        "app.listar_reservas",
        lambda: [{"id": RESERVA_ID, "estado": "Pendiente"}],
    )
    respuesta = client.get("/api/reservas", headers=headers())

    assert respuesta.status_code == 200
    assert respuesta.get_json()["total"] == 1


def test_listar_reservas_sin_token(client):
    respuesta = client.get("/api/reservas")
    assert respuesta.status_code == 403


def test_listar_reservas_error(client, monkeypatch):
    def fallo():
        raise RuntimeError("Error simulado")

    monkeypatch.setattr("app.listar_reservas", fallo)

    respuesta = client.get("/api/reservas", headers=headers())
    assert respuesta.status_code == 503