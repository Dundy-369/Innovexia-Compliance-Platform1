# Innovexia integrated prototype bundle

This bundle combines the supplied static frontend with the supplied FastAPI backend. FastAPI serves the frontend at `/site/` and the API at the root (for example `/health`, `/docs`, `/tenders`). The OCR upload helper now uses the same origin by default rather than `localhost`.

## Important status
This is an integration starter, **not a verified, production-ready final platform**. The frontend contains many prototype screens and sample/static UI; not every form/button has been connected to the API. The OCR engine was not supplied, so image OCR is not implemented here. The backend's database assumptions must be checked against your actual Supabase schema. Public deployment requires valid environment settings and end-to-end testing.

## Run locally
1. Install Python 3.10+.
2. Open `backend/` in a terminal.
3. Create and activate a virtual environment.
4. Run `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env` and set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and other values. Keep `.env private; never put the service-role key in frontend files or commit it.
6. Run `uvicorn main:app --reload` from `backend/`.
7. Open `http://127.0.0.1:8000/` (frontend) or `/docs` (API docs).

## Frontend Supabase config
Copy `frontend/assets/runtime-config.example.js` to `frontend/assets/runtime-config.js`, then set the Supabase project URL and **publishable/anon key**. Do not use a service-role key in the browser. The supplied HTML currently loads `assets/supabase.js`; add this line immediately before that script on pages requiring Supabase auth:

`<script src="assets/runtime-config.js"></script>`

If `runtime-config.js` is absent, the auth client will log a warning and authentication will not work.

## OCR and verification
The `/crosscheck/{document_type}` endpoint can process text-based PDF/TXT inputs in this prototype. Scanned PDFs and images need your teammate's OCR engine to be connected. Existing OCR rows can be used to test stored-record verification through `/verify/{bid_id}`. Use only synthetic/test records until the workflow is validated.

## Before public deployment
- Align table names/columns and storage bucket with your Supabase project.
- Configure CORS if frontend and API are hosted on different origins.
- Set secure authentication/authorization and row-level access controls; do not expose unrestricted service-role-backed operations.
- Wire each visible form/action to the appropriate API and handle errors/loading states.
- Test upload → extraction → reference verification → cross-document checks → compliance → officer decision with test users.
- Use HTTPS and a private storage bucket with appropriate policies.
