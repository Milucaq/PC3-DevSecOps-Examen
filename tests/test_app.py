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