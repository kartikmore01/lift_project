# Lift Project

Sab kuch ek Netlify site par chalta hai (https://bestlift.netlify.app):

- `public/index.html` -> Lift dashboard
- `public/camera-detector.html` -> webcam se crowd count (dashboard par "Open camera")
- `netlify/functions/api.mts` -> backend API (`/api/recommend`, `/api/status`, `/api/lift`, `/api/crowd`, `/api/maintenance`)
- `db/schema.ts` -> Netlify Database (Postgres) tables; migrations `netlify/database/migrations/` me
- `esp32_simulator.py` -> fake lift data

## Camera se Lift B aur C bhejna
Camera page kholo, floor chuno, "Start camera" dabao. Har 2 sec me people count backend ko jaata hai.
Agar 6 ya zyada log dikhe to Lift B aur Lift C us floor par apne aap bheji jaati hain
(maintenance wali lift nahi jaati). Lift har 3 sec me ek floor chalti hai aur dashboard par `→F<floor>` dikhta hai.

## Chalana
1. Deploy: GitHub `main` par push karo, Netlify khud build + DB migration karta hai.
2. Fake lifts: `pip install requests && python esp32_simulator.py` (default: https://bestlift.netlify.app/api)
3. Staff PIN: Netlify env var `ADMIN_PIN` set karo (default 1234).

`main.py` purana FastAPI backend hai; ab zaroori nahi.
