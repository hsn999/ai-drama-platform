from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, project_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(project_id, []).append(websocket)

    def disconnect(self, project_id: str, websocket: WebSocket) -> None:
        if project_id in self.active:
            self.active[project_id] = [ws for ws in self.active[project_id] if ws != websocket]

    async def broadcast(self, project_id: str, message: dict[str, Any]) -> None:
        for ws in self.active.get(project_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


ws_manager = ConnectionManager()


async def broadcast_progress(
    project_id: str, step: str, current: int, total: int, message: str
) -> None:
    percent = int(current / total * 100) if total else 0
    await ws_manager.broadcast(
        project_id,
        {
            "type": "progress",
            "step": step,
            "current": current,
            "total": total,
            "message": message,
            "percent": percent,
        },
    )
