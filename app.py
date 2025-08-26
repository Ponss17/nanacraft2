from flask import Flask, jsonify
from flask_cors import CORS
from mcstatus import JavaServer
import traceback

app = Flask(__name__)
CORS(app)

SERVER_IP = "23.230.3.73"
SERVER_PORT = 25615

@app.route('/')
def home():
    return jsonify({
        "message": "API de información del servidor de NaNaCraft.",
        "endpoints": {
            "/server/info": "Información general de NaNaCraft.",
            "/server/status": "Estado del servidor.",
            "/server/players": "Lista de jugadores conectados."
        }
    })

@app.route('/server/info')
def get_server_info():
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        status = server.status()
        
        return jsonify({
            "success": True,
            "server": {
                "ip": SERVER_IP,
                "port": SERVER_PORT,
                "version": status.version.name,
                "protocol": status.version.protocol,
                "players": {
                    "online": status.players.online,
                    "max": status.players.max,
                    "list": [player.name for player in status.players.sample] if status.players.sample else []
                },
                "description": status.description,
                "latency": status.latency,
                "favicon": status.favicon
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "No se pudo conectar al servidor"
        }), 500

@app.route('/server/status')
def get_server_status():
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        status = server.status()
        
        return jsonify({
            "success": True,
            "online": True,
            "players_online": status.players.online,
            "max_players": status.players.max,
            "latency": status.latency,
            "version": status.version.name
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "online": False,
            "error": str(e)
        }), 500

@app.route('/server/players')
def get_server_players():
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        status = server.status()
        
        players_string = ""
        if status.players.sample:
            players_names = [player.name for player in status.players.sample]
            players_string = ",".join(players_names)
        
        return jsonify({
            "success": True,
            "players": {
                "online": status.players.online,
                "max": status.players.max,
                "list": players_string
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "No se pudo obtener la lista de jugadores"
        }), 500

@app.route('/server/players/list')
def get_players_list_only():
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        status = server.status()
        
        if status.players.sample:
            players_names = [player.name for player in status.players.sample]
            return ",".join(players_names)
        else:
            return ""
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/server/ping')
def ping_server():
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        latency = server.ping()
        
        return jsonify({
            "success": True,
            "latency": latency,
            "message": f"Servidor responde en {latency:.2f}ms"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Servidor no responde."
        }), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))

    app.run(debug=False, host='0.0.0.0', port=port)




