import os
import time

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Lift Backend")

# Testing ke liye sab allow hai. Baad me "*" ki jagah apna Vercel URL daal sakte ho.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NUM_FLOORS = 6          # floor 0 se 5
SEC_PER_FLOOR = 3       # ek floor chadhne me kitne second
SEC_PER_PERSON = 1.5    # andar jitne log, utna extra time (stops ki wajah se)
COMFORT_WEIGHT = 2      # ranking me crowd ka asar (har insaan = 2 sec ka penalty)
CAPACITY = 10           # itne log ho to lift full
OFFLINE_AFTER = 20      # itne second data na aaye to lift offline
ADMIN_PIN = os.environ.get("ADMIN_PIN", "1234")  # maintenance badalne ka PIN

lifts = {
    i: {"id": i, "name": "ABC"[i - 1], "floor": 0, "direction": "idle",
        "load": 0, "updated": 0, "maintenance": False}
    for i in (1, 2, 3)
}
waiting = {}  # floor -> camera ne kitne log dekhe


class Lift(BaseModel):
    lift_id: int = 1
    floor: int
    direction: str
    load: int = 0


class Crowd(BaseModel):
    crowd_count: int
    floor: int = 0


class Maintenance(BaseModel):
    lift_id: int
    on: bool
    pin: str = ""


# ---- logic start ----
def eta_seconds(floor, direction, load, target):
    top = NUM_FLOORS - 1
    if direction == "idle" or floor == target:
        dist = abs(floor - target)
    elif direction == "up":
        dist = target - floor if target >= floor else (top - floor) + (top - target)
    else:  # down
        dist = floor - target if target <= floor else floor + target
    extra = load * SEC_PER_PERSON if dist > 0 else 0
    return round(dist * SEC_PER_FLOOR + extra)


def crowd_level(load):
    if load >= CAPACITY:
        return "full"
    if load >= 7:
        return "high"
    if load >= 4:
        return "medium"
    return "low"


def lift_status(l, online, level):
    if l["maintenance"]:
        return "maintenance"
    if not online:
        return "offline"
    if level == "full":
        return "full"
    return "ok"
# ---- logic end ----


def is_online(l):
    return l["updated"] > 0 and time.time() - l["updated"] <= OFFLINE_AFTER


@app.get("/")
def home():
    return {"message": "Lift backend chal raha hai. /recommend?floor=3 dekho."}


@app.get("/status")
def get_status():
    return {"lifts": list(lifts.values()), "waiting": waiting}


@app.post("/lift")
def set_lift(d: Lift):
    if d.lift_id not in lifts:
        raise HTTPException(404, "lift_id 1, 2 ya 3 hona chahiye")
    l = lifts[d.lift_id]
    l["floor"] = max(0, min(NUM_FLOORS - 1, d.floor))
    l["direction"] = d.direction if d.direction in ("up", "down", "idle") else "idle"
    l["load"] = max(0, d.load)
    l["updated"] = int(time.time())
    return l


@app.post("/crowd")
def set_crowd(d: Crowd):
    waiting[str(d.floor)] = max(0, d.crowd_count)
    return {"waiting": waiting}


@app.post("/maintenance")
def set_maintenance(d: Maintenance):
    if d.pin != ADMIN_PIN:
        raise HTTPException(403, "Galat PIN")
    if d.lift_id not in lifts:
        raise HTTPException(404, "lift_id 1, 2 ya 3 hona chahiye")
    lifts[d.lift_id]["maintenance"] = d.on
    return lifts[d.lift_id]


@app.get("/recommend")
def recommend(floor: int = Query(0, ge=0, le=NUM_FLOORS - 1)):
    out = []
    for l in lifts.values():
        online = is_online(l)
        level = crowd_level(l["load"])
        status = lift_status(l, online, level)
        eta = eta_seconds(l["floor"], l["direction"], l["load"], floor) if status == "ok" else None
        out.append({**l, "online": online, "crowd_level": level,
                    "capacity": CAPACITY, "status": status, "eta": eta})

    ok = [x for x in out if x["status"] == "ok"]
    # ranking: eta + crowd ka comfort penalty
    ok.sort(key=lambda x: (x["eta"] + x["load"] * COMFORT_WEIGHT, x["eta"]))
    ranking = [x["id"] for x in ok]
    best = ranking[0] if ranking else None

    reason = ""
    if ok:
        fastest = min(ok, key=lambda x: x["eta"])
        if ok[0]["id"] == fastest["id"]:
            reason = "Sabse jaldi pahunchegi"
        else:
            diff = ok[0]["eta"] - fastest["eta"]
            reason = f"Thodi der se (+{diff} sec) par kam bheed wali"
    else:
        reason = "Abhi koi lift available nahi hai"

    waiting_here = waiting.get(str(floor), 0)
    return {
        "floor": floor,
        "best": best,
        "ranking": ranking,
        "reason": reason,
        "lifts": out,
        "waiting_here": waiting_here,
        "floor_crowded": waiting_here >= 6,
        "waiting": waiting,
    }
