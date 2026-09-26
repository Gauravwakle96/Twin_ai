# Deployment Instructions

## Render (Backend)
1. Create a **Web Service** in Render, connect your GitHub repo.
2. Set **Root Directory** to `backend`.
3. Set **Start Command** to:
   ```
   gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 wsgi:app
   ```
   (Use `wsgi:app` — NOT `backend.main:app` — because the Root Directory is `backend`, so the working directory is already inside `backend/`.)
4. Set **Build Command** to `pip install -r requirements.txt`.
5. Deploy.

## Vercel (Frontend)
- Import the same repo, set **Root Directory** to `frontend`, framework `Vite`, and deploy.
- Set the environment variable `VITE_API_URL` to your Render service URL.
