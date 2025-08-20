# API de Información de Servidor Minecraft

Esta API proporciona información en tiempo real del servidor de Minecraft ubicado en `23.230.3.73:25615`.

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecuta la API:
```bash
python app.py
```

La API estará disponible en `http://localhost:5000`

## Endpoints Disponibles

### GET `/`
Muestra información general de la API y endpoints disponibles.

### GET `/server/info`
Devuelve información completa del servidor:
- Versión del servidor
- Jugadores conectados
- Descripción del servidor
- Latencia
- Favicon (si está disponible)

### GET `/server/status`
Devuelve el estado básico del servidor:
- Si está online
- Número de jugadores conectados
- Latencia

### GET `/server/players`
Devuelve la lista de jugadores conectados (si está disponible).

### GET `/server/ping`
Realiza un ping al servidor y devuelve la latencia.

## Ejemplo de Respuesta

```json
{
  "success": true,
  "server": {
    "ip": "23.230.3.73",
    "port": 25615,
    "version": "1.20.1",
    "players": {
      "online": 5,
      "max": 20,
      "list": ["Player1", "Player2"]
    },
    "description": "Mi servidor de Minecraft",
    "latency": 45.2
  }
}
```

## Manejo de Errores

Si el servidor no está disponible o hay algún error, la API devuelve:

```json
{
  "success": false,
  "error": "Descripción del error",
  "message": "Mensaje explicativo"
}
```