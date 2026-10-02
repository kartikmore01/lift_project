import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Lift Backend")

# Testing ke liye sab allow hai. Deploy ke baad "*" ki jagah apna Vercel URL daal sakte ho.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

state = {"floor": 0, "direction": "idle", "crowd_count": 0, "updated": 0}


class Lift(BaseModel):
    floor: int
    direction: str


class Crowd(BaseModel):
    crowd_count: int


@app.get("/")
def home():
    return {"message": "Lift backend chal raha hai. /status dekho."}


@app.get("/status")
def get_status():
    return state


@app.post("/lift")
def set_lift(d: Lift):
    state["floor"] = d.floor
    state["direction"] = d.direction
    state["updated"] = int(time.time())
    return state


@app.post("/crowd")
def set_crowd(d: Crowd):
    state["crowd_count"] = d.crowd_count
    state["updated"] = int(time.time())
    return state
