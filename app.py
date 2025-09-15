from flask import Flask, jsonify
from flask_cors import CORS
from mcstatus import JavaServer
import os
from functools import wraps
import signal
from contextlib import contextmanager

app = Flask(__name__)
CORS(app)

SERVER_IP = "23.230.3.74"
SERVER_PORT = 25770
SERVER_ADDRESS = f"{SERVER_IP}:{SERVER_PORT}"
SERVER_NAME = "NaNaCraft2"

@contextmanager
def timeout_handler(seconds):
    def timeout_signal(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_signal)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def handle_server_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            with timeout_handler(10):
                return f(*args, **kwargs)
        except TimeoutError:
            return jsonify({
                "success": False,
                "error": "Request timeout",
                "message": f"La consulta a {SERVER_NAME} tardó demasiado"
            }), 504
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "message": f"Error al conectar con {SERVER_NAME}"
            }), 500
    return decorated_function

def get_server():
    return JavaServer.lookup(SERVER_ADDRESS)

def format_players(players_sample):
    if not players_sample:
        return []
    
    return [{
        "name": player.name,
        "uid": player.id,
        "avatar": {
            "small": f"https://crafatar.com/avatars/{player.id}?size=32",
            "medium": f"https://crafatar.com/avatars/{player.id}?size=64",
            "large": f"https://crafatar.com/avatars/{player.id}?size=128",
            "head_3d": f"https://crafatar.com/renders/head/{player.id}?size=64",
            "body_3d": f"https://crafatar.com/renders/body/{player.id}?size=64"
        },
        "skin": {
            "url": f"https://crafatar.com/skins/{player.id}",
            "cape_url": f"https://crafatar.com/capes/{player.id}"
        }
    } for player in players_sample]

@app.route('/')
def home():
    return jsonify({
        "message": f"API de información del servidor {SERVER_NAME}",
        "server": {
            "name": SERVER_NAME,
            "ip": SERVER_IP,
            "port": SERVER_PORT
        },
        "endpoints": {
            "/server/info": "Información completa del servidor",
            "/server/status": "Estado básico del servidor",
            "/server/players": "Lista completa de jugadores",
            "/server/ping": "Latencia del servidor"
        }
    })

@app.route('/server/info')
@handle_server_errors
def get_server_info():
    server = get_server()
    status = server.status()
    
    return jsonify({
        "success": True,
        "server": {
            "name": SERVER_NAME,
            "ip": SERVER_IP,
            "port": SERVER_PORT,
            "version": status.version.name,
            "protocol": status.version.protocol,
            "description": status.description,
            "latency": status.latency,
            "favicon": status.favicon,
            "players": {
                "online": status.players.online,
                "max": status.players.max,
                "list": format_players(status.players.sample)
            }
        }
    })

@app.route('/server/status')
@handle_server_errors
def get_server_status():
    server = get_server()
    status = server.status()
    
    return jsonify({
        "success": True,
        "online": True,
        "server_name": SERVER_NAME,
        "players_online": status.players.online,
        "max_players": status.players.max,
        "latency": status.latency,
        "version": status.version.name
    })

@app.route('/server/players')
@handle_server_errors
def get_server_players():
    server = get_server()
    status = server.status()
    
    players_detailed = format_players(status.players.sample)
    players_names = [player.name for player in status.players.sample] if status.players.sample else []
    
    return jsonify({
        "success": True,
        "server_name": SERVER_NAME,
        "players": {
            "online": status.players.online,
            "max": status.players.max,
            "count": len(players_names),
            "list": players_detailed,
            "names_only": players_names,
            "names_string": ",".join(players_names) if players_names else "No hay jugadores conectados"
        }
    })

@app.route('/server/ping')
@handle_server_errors
def ping_server():
    server = get_server()
    latency = server.ping()
    
    return jsonify({
        "success": True,
        "server_name": SERVER_NAME,
        "latency": latency,
        "message": f"{SERVER_NAME} responde en {latency:.2f}ms"
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint no encontrado",
        "message": "Verifica la URL y los endpoints disponibles en '/'",
        "server": SERVER_NAME
    }), 404

@app.errorhandler(504)
def gateway_timeout(error):
    return jsonify({
        "success": False,
        "error": "Gateway timeout",
        "message": "El servidor tardó demasiado en responder",
        "server": SERVER_NAME
    }), 504

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

##Vivan las chichonas :)
