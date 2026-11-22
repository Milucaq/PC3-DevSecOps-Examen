import os
from datetime import datetime
from hmac import compare_digest
from http.client import HTTPException

from flask import Flask, jsonify, render_template, request

from supabase_client import guardar_embarcacion, obtener_puntos

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/pescador")
def portal_pescador():
    return render_template("pescador.html")

@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "API Flask funcionando",
    })


@app.route("/api/puntos")
def listar_puntos():
    try:
        puntos = obtener_puntos()

        return jsonify({
            "status": "ok",
            "total": len(puntos),
            "datos": puntos,
        })

    except (HTTPException, OSError, ValueError, TypeError, RuntimeError):
        app.logger.exception("Error al consultar Supabase")

        return jsonify({
            "status": "error",
            "message": "No se pudieron consultar los puntos",
        }), 503
@app.route("/api/embarcaciones", methods=["POST"])
def registrar_embarcacion():
    datos = request.get_json(silent=True)

    if not isinstance(datos, dict):
        return jsonify({
            "status": "error",
            "message": "Debes enviar un objeto JSON válido",
        }), 400

    nombre_embarcacion = datos.get("nombre_embarcacion")
    nombre_pescador = datos.get("nombre_pescador")
    llegada_estimada = datos.get("llegada_estimada")
    estado = datos.get("estado", "En faena")

    if not all([
        isinstance(nombre_embarcacion, str),
        isinstance(nombre_pescador, str),
        isinstance(llegada_estimada, str),
        isinstance(estado, str),
    ]):
        return jsonify({
            "status": "error",
            "message": "Todos los campos deben ser textos válidos",
        }), 400

    nombre_embarcacion = nombre_embarcacion.strip()
    nombre_pescador = nombre_pescador.strip()

    if not (
        2 <= len(nombre_embarcacion) <= 120
        and 2 <= len(nombre_pescador) <= 120
    ):
        return jsonify({
            "status": "error",
            "message": "Los nombres deben tener entre 2 y 120 caracteres",
        }), 400

    if estado not in ("En faena", "Regresando", "Arribó"):
        return jsonify({
            "status": "error",
            "message": "Estado de embarcación no válido",
        }), 400

    try:
        fecha = datetime.fromisoformat(
            llegada_estimada
        )
        if fecha.tzinfo is None or fecha.utcoffset() is None:
            raise ValueError("Falta zona horaria")
    except ValueError:
        return jsonify({
            "status": "error",
            "message": "La fecha debe incluir zona horaria",
        }), 400

    token_configurado = os.getenv("PESCACONECTA_ADMIN_TOKEN", "")
    token_recibido = request.headers.get("X-Admin-Token", "")

    if not token_configurado or not compare_digest(
        token_recibido, token_configurado
    ):
        return jsonify({
            "status": "error",
            "message": "No autorizado",
        }), 403

    try:
        registro = guardar_embarcacion({
            "nombre_embarcacion": nombre_embarcacion,
            "nombre_pescador": nombre_pescador,
            "llegada_estimada": fecha.isoformat(),
            "estado": estado,
        })
    except (HTTPException, OSError, ValueError, TypeError, RuntimeError):
        app.logger.exception("Error al guardar embarcacion")
        return jsonify({
            "status": "error",
            "message": "No se pudo guardar la embarcacion",
        }), 503

    return jsonify({
        "status": "ok",
        "message": "Embarcacion registrada",
        "datos": registro,
    }), 201




if __name__ == "__main__":
    app.run()