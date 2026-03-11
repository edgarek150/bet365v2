import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from models import app_state
from utils.io import load_json_from_file
import config

monitoring_app = FastAPI()

monitoring_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@monitoring_app.get("/status")
def get_status():
    data = load_json_from_file(config.DATA_JSON) or []

    tournaments = []
    for tourn in data:
        for event in tourn.get("events", []):
            matches = []
            for m in event.get("matches", []):
                if len(m) >= 4:
                    matches.append({
                        "player1": m[0],
                        "player2": m[1],
                        "odd1": m[2],
                        "odd2": m[3],
                    })
            tournaments.append({
                "tournament": tourn["name"],
                "event": event["name"],
                "matches": matches,
            })

    return {
        "status": "running",
        "loops_counter": app_state.LOOPS_COUNTER,
        "active_events": len(app_state.URLS),
        "last_seen": app_state.last_seen.isoformat() if app_state.last_seen else None,
        "tournaments": tournaments,
    }


async def start_monitoring(port: int = 8080):
    cfg = uvicorn.Config(monitoring_app, host="0.0.0.0", port=port, log_level="warning")
    server = uvicorn.Server(cfg)
    await server.serve()
