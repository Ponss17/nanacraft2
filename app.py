from flask import Flask, jsonify
from flask_cors import CORS
from mcstatus import JavaServer
from mcrcon import MCRcon
import os
from functools import wraps
import time
from threading import Lock

app = Flask(__name__)
CORS(app)

SERVER_IP = "23.230.3.73"
SERVER_PORT = 25615
SERVER_ADDRESS = f"{SERVER_IP}:{SERVER_PORT}"
SERVER_NAME = "NaNaCraft2"

RCON_HOST = SERVER_IP
RCON_PORT = int(os.environ.get('RCON_PORT', 25575))
RCON_PASSWORD = os.environ.get('RCON_PASSWORD', 'default_password')

class CacheManager:
    def __init__(self):
        self.players_cache = {}
        self.cache_lock = Lock()
        self.rcon_request_count = 0
        self.last_reset_time = time.time()
        self.CACHE_DURATION = 60
        self.MAX_RCON_REQUESTS_PER_MINUTE = 10
    
    def rate_limit_rcon(self):
        with self.cache_lock:
            current_time = time.time()
            if current_time - self.last_reset_time > 60:
                self.rcon_request_count = 0
                self.last_reset_time = current_time
            
            if self.rcon_request_count >= self.MAX_RCON_REQUESTS_PER_MINUTE:
                return False
            
            self.rcon_request_count += 1
            return True
    
    def get_cached_player_data(self, player_name):
        with self.cache_lock:
            current_time = time.time()
            
            if (player_name in self.players_cache and 
                current_time - self.players_cache[player_name]['timestamp'] < self.CACHE_DURATION):
                return self.players_cache[player_name]['data']
            
            if not self.rate_limit_rcon():
                if player_name in self.players_cache:
                    return self.players_cache[player_name]['data']
                else:
                    return {"error": "Rate limit excedido, intenta más tarde"}
            
            essentials_data = self._get_player_essentials_data_direct(player_name)
            
            self.players_cache[player_name] = {
                'data': essentials_data,
                'timestamp': current_time
            }
            
            return essentials_data
    
    def _get_player_essentials_data_direct(self, player_name):
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT, timeout=5) as mcr:
                commands = {
                    "balance": f"bal {player_name}",
                    "playtime": f"playtime {player_name}",
                    "last_seen": f"seen {player_name}"
                }
                
                player_data = {}
                for key, command in commands.items():
                    try:
                        response = mcr.command(command)
                        player_data[key] = response
                    except Exception:
                        player_data[key] = "No disponible"
                
                return player_data
        except Exception as e:
            return {"error": f"RCON no disponible: {str(e)}"}

cache_manager = CacheManager()

def handle_server_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
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
    
    players_list = []
    for player in players_sample:
        player_info = {
            "name": player.name,
            "uid": player.id,
            "display_name": player.name,
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
        }
        
        essentials_data = cache_manager.get_cached_player_data(player.name)
        player_info["essentials"] = essentials_data
        
        players_list.append(player_info)
    
    return players_list

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
            "/server/players": "Lista completa de jugadores (detallada y simple)",
            "/server/ping": "Latencia del servidor"
        },
        "features": {
            "cache": "Sistema de caché optimizado (60s)",
            "rate_limit": "Máximo 10 requests RCON por minuto",
            "essentials": "Integración con EssentialsX"
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
    
#Vivan las chichonas :)
