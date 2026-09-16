import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# Admin chat or group ID (can be user ID e.g. 123456789 or group ID e.g. -100123456789)
raw_admin_id = os.getenv("ADMIN_CHAT_ID", "0").strip()
try:
    ADMIN_CHAT_ID = int(raw_admin_id)
except ValueError:
    ADMIN_CHAT_ID = 0

# Optional: Specific Forum Topic ID (thread_id) in a Supergroup
raw_topic_id = os.getenv("ADMIN_TOPIC_ID", "0").strip()
try:
    ADMIN_TOPIC_ID = int(raw_topic_id)
except ValueError:
    ADMIN_TOPIC_ID = 0

DEFAULT_AUTO_REPLY = os.getenv(
    "DEFAULT_AUTO_REPLY",
    "Hello! Thank you for contacting us. We have received your message and will get back to you shortly."
).strip('"\'')

# Modes: 'first_time', 'always', 'disabled'
AUTO_REPLY_MODE = os.getenv("AUTO_REPLY_MODE", "first_time").strip().lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Admin priority waiting time before AI auto-answers (in seconds, default 60s / 1 min)
ADMIN_REPLY_TIMEOUT_SECONDS = int(os.getenv("ADMIN_REPLY_TIMEOUT_SECONDS", "60"))

DB_PATH = BASE_DIR / "bot_data.db"
KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base.txt"
