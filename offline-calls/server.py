"""Servidor para el Sistema de llamadas: sirve la app y hace de
señalización WebRTC + relay de chat para la pestaña "Video llamada grupal".

El registro de llamadas offline sigue funcionando desde el navegador con
localStorage y no depende de este servidor; solo la pestaña de video
llamada y chat en vivo lo necesita, porque dos navegadores no pueden
encontrarse ni intercambiar audio/video sin un intermediario.
"""

import io
import uuid
from pathlib import Path
from typing import Dict

import qrcode
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

app = FastAPI(title="Sistema de llamadas")

BASE_DIR = Path(__file__).parent
INDEX_FILE = BASE_DIR / "index.html"

# room_id -> {client_id: WebSocket}
rooms: Dict[str, Dict[str, WebSocket]] = {}
# room_id -> {client_id: display_name}
names: Dict[str, Dict[str, str]] = {}


@app.get("/")
async def index():
    return FileResponse(INDEX_FILE)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/qr")
async def qr_code(data: str):
    """Genera un QR con el link a una sala, para invitar sin escribir nada.
    No queda guardado en ningun lado: se genera al vuelo en cada pedido."""
    img = qrcode.make(data, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.websocket("/ws/{room_id}")
async def signaling(websocket: WebSocket, room_id: str):
    await websocket.accept()
    client_id = str(uuid.uuid4())[:8]
    display_name = websocket.query_params.get("name") or f"Usuario-{client_id}"

    room = rooms.setdefault(room_id, {})
    room_names = names.setdefault(room_id, {})

    existing_peers = [{"id": pid, "name": room_names[pid]} for pid in room]

    room[client_id] = websocket
    room_names[client_id] = display_name

    await websocket.send_json(
        {"type": "welcome", "id": client_id, "peers": existing_peers}
    )

    for pid, ws in room.items():
        if pid != client_id:
            await ws.send_json(
                {"type": "peer-joined", "id": client_id, "name": display_name}
            )

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "chat":
                for pid, ws in room.items():
                    if pid != client_id:
                        await ws.send_json(
                            {
                                "type": "chat",
                                "from": display_name,
                                "message": data.get("message", ""),
                            }
                        )
            elif msg_type in ("offer", "answer", "ice-candidate"):
                target_ws = room.get(data.get("target"))
                if target_ws:
                    payload = dict(data)
                    payload["from"] = client_id
                    await target_ws.send_json(payload)
    except WebSocketDisconnect:
        pass
    finally:
        room.pop(client_id, None)
        room_names.pop(client_id, None)
        for ws in list(room.values()):
            try:
                await ws.send_json({"type": "peer-left", "id": client_id})
            except Exception:
                pass
        if not room:
            rooms.pop(room_id, None)
            names.pop(room_id, None)
