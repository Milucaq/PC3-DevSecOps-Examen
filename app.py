from http.client import HTTPException

from flask import Flask, jsonify, render_template

from supabase_client import obtener_puntos

app = Flask(__name__)


@app.route("/")
def inicio():
    return render_template("index.html")


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


if __name__ == "__main__":
    app.run()