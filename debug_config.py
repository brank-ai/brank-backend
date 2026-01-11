
import os
from config import Settings

# Simulate the exact environment variables user has in Cloud Run (based on screenshot)
# Note: We won't put real keys here to avoid leaking them, but we set MIN_LLM_COUNT to 2
os.environ["MIN_LLM_COUNT"] = "2"
os.environ["DATABASE_URL"] = "postgresql+psycopg2://postgres:postgres@/brank_db?host=/cloudsql/some-connection"
# We deliberately DON'T set valid keys to see if the validation logic is what's failing

print("Attemping to load Settings...")
try:
    s = Settings()
    print("SUCCESS!")
    print(s.model_dump())
except Exception as e:
    print(f"FAILURE: {e}")
