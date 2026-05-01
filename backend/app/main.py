from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, engine, get_db, SessionLocal
from app.models import ActionEvent, ApprovalState
from app.schemas import ActionEventResponse, DashboardPayload
from app.seed import seed_database
from app.services import DashboardBroadcaster, run_simulation, serialize_dashboard

settings = get_settings()
broadcaster = DashboardBroadcaster()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        seed_database(session)

    simulation_task = asyncio.create_task(run_simulation(broadcaster))
    try:
        yield
    finally:
        simulation_task.cancel()
        with suppress(asyncio.CancelledError):
            await simulation_task


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/dashboard", response_model=DashboardPayload)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardPayload:
    return serialize_dashboard(db)


@app.post("/api/actions/{action_id}/approve", response_model=ActionEventResponse)
async def approve_action(action_id: int, db: Session = Depends(get_db)) -> ActionEventResponse:
    action = db.get(ActionEvent, action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != ApprovalState.required:
        raise HTTPException(status_code=400, detail="Action does not require approval")

    action.status = ApprovalState.approved
    db.commit()
    db.refresh(action)
    await broadcaster.broadcast(serialize_dashboard(db).model_dump(mode="json"))
    return ActionEventResponse.model_validate(action, from_attributes=True)


@app.websocket("/ws/dashboard")
async def dashboard_socket(websocket: WebSocket) -> None:
    await broadcaster.connect(websocket)
    try:
        with SessionLocal() as session:
            await websocket.send_json(serialize_dashboard(session).model_dump(mode="json"))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(websocket)
    except Exception:
        broadcaster.disconnect(websocket)
