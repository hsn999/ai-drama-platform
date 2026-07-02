from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.character import router as character_router
from api.character_library import router as library_router
from api.media import router as media_router
from api.music import router as music_router
from api.mv import router as mv_router
from api.project import router as project_router
from api.settings import router as settings_router
from api.task import router as task_router
from api.websocket import ws_manager
from config import get_settings
from database import Base, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="AI Drama Factory", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_router, prefix="/api")
app.include_router(character_router, prefix="/api")
app.include_router(library_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(music_router, prefix="/api")
app.include_router(mv_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/api/health")
async def health():
    from comfyui.api import comfyui_client
    from hardware_profiles import get_profile
    from video.ffmpeg import ffmpeg_available
    import httpx

    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    profile = get_profile()
    return {
        "status": "ok",
        "ollama": ollama_ok,
        "comfyui": await comfyui_client.is_available(),
        "ffmpeg": ffmpeg_available(),
        "hardware_profile": profile.to_dict(),
    }


@app.websocket("/ws/progress/{project_id}")
async def websocket_progress(project_id: str, websocket: WebSocket):
    await ws_manager.connect(project_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(project_id, websocket)
