from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import logging


class ConnectionManager:
    """Keeps track of active websocket connections per user and provides helpers
    to send/broadcast JSON payloads. A global instance (`manager`) is created at
    the bottom of this file and can safely be imported anywhere in the project.
    """

    def __init__(self):
        # user_id -> set of websocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None

    async def connect(self, user_id: str, websocket: WebSocket):
        if self._loop is None or not self._loop.is_running():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        conns = self._connections.get(user_id)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self._connections.pop(user_id, None)

    async def _safe_send(self, ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except Exception as exc:
            logging.exception("WebSocket send failed", exc_info=exc)
            await self._close_ws(ws)

    async def send_personal(self, user_id: str, data: dict):
        for ws in list(self._connections.get(user_id, [])):
            await self._safe_send(ws, data)

    async def broadcast(self, user_ids: List[str], data: dict):
        tasks = [self.send_personal(uid, data) for uid in set(user_ids)]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def _ensure_loop(self):
        if self._loop and self._loop.is_running():
            return self._loop
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        return self._loop

    def ts_send_personal(self, user_id: str, data: dict):
        loop = self._ensure_loop()
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.send_personal(user_id, data), loop)

    def ts_broadcast(self, user_ids: List[str], data: dict):
        loop = self._ensure_loop()
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(user_ids, data), loop)

    async def _close_ws(self, ws: WebSocket):
        try:
            await ws.close()
        except Exception:
            pass


manager = ConnectionManager() 