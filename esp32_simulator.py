"""Fake ESP32: lift ki movement backend ko bhejta hai.
Chalane ka tareeka:
    pip install requests
    python esp32_simulator.py                       (local backend)
    python esp32_simulator.py https://tumhara-app.onrender.com   (deployed backend)
"""
import random
import sys
import time

import requests

API = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://localhost:8000"
floor = 0
print("Sending to", API)

while True:
    new = random.randint(0, 5)
    direction = "up" if new > floor else "down" if new < floor else "idle"
    floor = new
    try:
        requests.post(API + "/lift", json={"floor": floor, "direction": direction}, timeout=60)
        print("sent: floor", floor, direction)
    except Exception as e:
        print("error:", e)
    time.sleep(3)
