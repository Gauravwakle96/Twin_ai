# Deployment Instructions

## Render (Backend)
The service is configured with **Root Directory = repo root** (so the working
directory at runtime is `/opt/render/project/src/`, not `backend/`).

1. In your Render Web Service, set the **Start Command** to:
   ```
   gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 backend.wsgi:app
   ```
   Use `backend.wsgi:app` (not `wsgi:app` and not `backend.main:app`).
   `backend/wsgi.py` inserts the project root onto `sys.path` so the absolute
   imports inside `backend/main.py` resolve no matter the working directory.
2. **Build Command**: `pip install -r backend/requirements.txt`
3. Deploy.

## Vercel (Frontend)
- Import the same repo, set **Root Directory** to `frontend`, framework `Vite`.
- Set environment variable `VITE_API_URL` to your Render service URL.
