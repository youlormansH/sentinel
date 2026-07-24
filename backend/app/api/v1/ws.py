from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from jose import JWTError

from app.core.security import decode_token
from app.ws.manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/alerts")
async def alerts_socket(websocket: WebSocket, token: str = ""):
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
    except (ValueError, JWTError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Clients don't need to send anything; just keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
