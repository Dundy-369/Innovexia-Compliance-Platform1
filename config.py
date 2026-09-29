import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "bidder-documents").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
CORS_ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]

def validate_config():
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is missing. Copy .env.example to .env and configure it.")
    if not SUPABASE_SERVICE_ROLE_KEY or "PASTE_YOUR" in SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is missing. Add your Supabase secret/service_role key to backend .env only.")
