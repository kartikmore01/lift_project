# Lift Project

- backend/  -> FastAPI (Render par deploy)
- frontend/ -> dashboard (Vercel par deploy)
- esp32_simulator.py -> fake lift data
- camera-detector.html -> webcam se crowd count

## Local chalana
1. cd backend && pip install -r requirements.txt && uvicorn main:app --reload
2. frontend/index.html browser me kholo
3. naye terminal me: pip install requests && python esp32_simulator.py
4. camera-detector.html kholo, Start camera dabao

## Deploy
Backend (Render): Root Directory = backend
  Build: pip install -r requirements.txt
  Start: uvicorn main:app --host 0.0.0.0 --port $PORT
Frontend (Vercel): Root Directory = frontend
  Deploy ke baad frontend/config.js me Render URL daalo, commit + push karo.
