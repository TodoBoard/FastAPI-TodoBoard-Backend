from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.auth.token import verify_token
from app.database.db import SessionLocal
from app.models.user import User
from app.websockets.connection_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.close(code=1008)
        return

    payload = verify_token(token)
    if payload is None:
        await websocket.close(code=1008)
        return

    username = payload.get("sub")
    if username is None:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            await websocket.close(code=1008)
            return

        await manager.connect(user.id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(user.id, websocket)
    finally:
        db.close() 