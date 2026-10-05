"""Fake ESP32: 3 lifts ki movement backend ko bhejta hai.
Chalane ka tareeka:
    python -m pip install requests
    python esp32_simulator.py                                   (local backend)
    python esp32_simulator.py https://tumhara-app.onrender.com  (deployed backend)
"""
import random
import sys
import time

import requests

API = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
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
            requests.post(API + "/lift", timeout=60, json={
                "lift_id": l["id"], "floor": l["floor"],
                "direction": direction, "load": l["load"]})
            print(f"lift {l['id']}: floor {l['floor']} {direction} load {l['load']}")
        except Exception as e:
            print("error:", e)
    time.sleep(2)
