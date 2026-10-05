"""Fake ESP32: 3 lifts ki movement backend ko bhejta hai.
Chalane ka tareeka:
    python -m pip install requests
    python esp32_simulator.py                                   (Netlify backend: https://bestlift.netlify.app/api)
    python esp32_simulator.py http://localhost:8888/api         (netlify dev)
    python esp32_simulator.py http://localhost:8000             (purana local FastAPI)
"""
import random
import sys
import time

import requests

API = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "https://bestlift.netlify.app/api"
print("Sending to", API)

lifts = [
    {"id": i, "floor": random.randint(0, 5), "target": random.randint(0, 5),
     "load": random.randint(0, 6), "pause": 0}
    for i in (1, 2, 3)
]

while True:
    for l in lifts:
        if l["pause"] > 0:
            l["pause"] -= 1
            direction = "idle"
        elif l["floor"] == l["target"]:
            l["pause"] = random.randint(1, 3)
            l["target"] = random.randint(0, 5)
            l["load"] = random.randint(0, 12)   # 10+ = lift full
            direction = "idle"
        elif l["target"] > l["floor"]:
            l["floor"] += 1
            direction = "up"
        else:
            l["floor"] -= 1
            direction = "down"
        try:
            r = requests.post(API + "/lift", timeout=60, json={
                "lift_id": l["id"], "floor": l["floor"],
                "direction": direction, "load": l["load"]})
            d = r.json()
            if d.get("dispatch_floor") is not None:
                # camera ne bheed dekh ke lift bheji hai: backend hi chala raha hai, hum uski position follow karte hain
                l["floor"], l["target"], l["pause"] = d["floor"], d["dispatch_floor"], 0
                print(f"lift {l['id']}: dispatched -> floor {d['dispatch_floor']} (abhi {d['floor']})")
                continue
            print(f"lift {l['id']}: floor {l['floor']} {direction} load {l['load']}")
        except Exception as e:
            print("error:", e)
    time.sleep(2)
