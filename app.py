from flask import Flask, jsonify
from flask_cors import CORS
from mcstatus import JavaServer
import traceback
import os
import time
import requests

app = Flask(__name__)
CORS(app)

SERVER_IP = os.getenv("SERVER_IP", "23.230.3.73")
SERVER_PORT = int(os.getenv("SERVER_PORT", 25615))

def get_server():
    return JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")

def response(success: bool, data=None, error=None, status_code=200):
    return jsonify({
        "success": success,
        "data": data,
        "error": error
    }), status_code

# Cache simple para status (5s)
cache = {"last_check": 0, "status": None}

def get_status_cached():
    now = time.time()
    if now - cache["last_check"] < 5 and cache["status"]:
        return cache["status"]
    server = get_server()
    status = server.status()
    cache["status"] = status
    cache["last_check"] = now
    return status

def get_player_data(name):
    """Obtiene datos extra (uuid y avatar) desde Mojang API"""
    try:
        url = f"https://api.mojang.com/users/profiles/minecraft/{name}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            uuid = data.get("id")
            avatar = f"https://crafatar.com/avatars/{uuid}?overlay"
            return {
                "name": name,
                "uuid": uuid,
                "avatar": avatar
            }
    except Exception as e:
        return {"name": name, "uuid": None, "avatar": None, "error": str(e)}
    return {"name": name, "uuid": None, "avatar": None}


@app.route('/')
def home():
    return response(True, {
        "message": "API de información del servidor de NaNaCraft.",
        "endpoints": {
            "/server/info": "Información general de NaNaCraft.",
            "/server/status": "Estado del servidor.",
            "/server/players": "Lista detallada de jugadores conectados.",
            "/server/players/list": "Solo la lista de jugadores (texto plano).",
            "/server/ping": "Realiza un ping al servidor"
        }
    })

@app.route('/server/info')
def get_server_info():
    try:
        status = get_status_cached()
        data = {
            "ip": SERVER_IP,
            "port": SERVER_PORT,
            "version": status.version.name,
            "protocol": status.version.protocol,
            "players": {
                "online": status.players.online,
                "max": status.players.max,
                "list": [p.name for p in status.players.sample] if status.players.sample else []
            },
            "description": str(status.description),
            "latency": status.latency,
            "favicon": status.favicon
        }
        return response(True, data)
    except Exception as e:
        traceback.print_exc()
        return response(False, error=str(e), status_code=500)

@app.route('/server/status')
def get_server_status():
    try:
        status = get_status_cached()
        data = {
            "online": True,
            "players_online": status.players.online,
            "max_players": status.players.max,
            "latency": status.latency,
            "version": status.version.name
        }
        return response(True, data)
    except Exception as e:
        traceback.print_exc()
        return response(False, {"online": False}, str(e), 500)

@app.route('/server/players')
def get_server_players():
    try:
        status = get_status_cached()
        players = []
        if status.players.sample:
            for p in status.players.sample:
                players.append(get_player_data(p.name))

        data = {
            "online": status.players.online,
            "max": status.players.max,
            "players": players
        }
        return response(True, data)
    except Exception as e:
        traceback.print_exc()
        return response(False, error=str(e), status_code=500)

@app.route('/server/players/list')
def get_players_list_only():
    try:
        status = get_status_cached()
        if status.players.sample:
            return ",".join([p.name for p in status.players.sample])
        return ""
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/server/ping')
def ping_server():
    try:
        server = get_server()
        latency = server.ping()
        return response(True, {
            "latency": latency,
            "message": f"Servidor responde en {latency:.2f}ms"
        })
    except Exception as e:
        traceback.print_exc()
        return response(False, error=str(e), status_code=500)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
