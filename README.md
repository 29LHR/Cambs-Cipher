# Cambs Cipher

Simple Flask web app for running the Cambs Cipher.

Quick start (development)

- Create a virtual environment and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

- Run the app (development, HTTP):

```bash
python3 app.py
```

By default the app binds to `0.0.0.0:5500` (see `FLASK_PORT` / `FLASK_BIND` env vars).

Notes about the current simplified configuration

- This workspace has been simplified for basic local development:
  - CSRF is disabled (`WTF_CSRF_ENABLED = False`).
  - `SESSION_COOKIE_SECURE` is set to `False` so cookies work over HTTP.
  - The `@app.after_request` security headers were removed.
  - The startup logic was simplified to always run HTTP (no SSL lookups).
- These changes are intended for local/dev use only. To restore HTTPS/CSRF/security headers, inspect and modify `app.py`.

Structure

- `app.py` — main Flask application and routes
- `forms.py` — WTForms definitions
- `templates/` — HTML templates
- `static/` — static assets
- `requirements.txt` — Python dependencies

Run the app (using Gunicorn):
```bash
bash run.sh
```
