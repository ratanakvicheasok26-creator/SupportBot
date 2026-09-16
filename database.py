import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import DB_PATH, DEFAULT_AUTO_REPLY, AUTO_REPLY_MODE

async def init_db():
    """Initialize SQLite database tables and migrations."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                topic_id INTEGER DEFAULT NULL,
                chat_mode TEXT DEFAULT 'ai',
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        """)

        # Migration: ensure chat_mode column exists on existing databases
        try:
            await db.execute("ALTER TABLE users ADD COLUMN chat_mode TEXT DEFAULT 'ai'")
        except Exception:
            pass  # Column already exists

        await db.execute("""
            CREATE TABLE IF NOT EXISTS message_mappings (
                admin_message_id INTEGER PRIMARY KEY,
                customer_chat_id INTEGER NOT NULL,
                customer_message_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL,
                text_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Self-correction and learning memory table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS learned_corrections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT,
                guidance TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Set default settings if not exists
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("auto_reply_text", "Hey there! 👋 Thanks for reaching out. How can I help you today?")
        )
        await db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            ("auto_reply_mode", AUTO_REPLY_MODE)
        )

        await db.commit()

async def get_setting(key: str, default: str = "") -> str:
    """Get a setting value."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default

async def set_setting(key: str, value: str):
    """Set or update a setting value."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()

async def upsert_user(user_id: int, first_name: str, last_name: Optional[str], username: Optional[str]) -> bool:
    """
    Insert or update a user record.
    Returns True if this is a brand new user, False otherwise.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, message_count FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()

        now = datetime.now().isoformat()
        if row is None:
            await db.execute("""
                INSERT INTO users (user_id, first_name, last_name, username, chat_mode, first_seen, last_seen, message_count)
                VALUES (?, ?, ?, ?, 'ai', ?, ?, 1)
            """, (user_id, first_name, last_name, username, now, now))
            await db.commit()
            return True
        else:
            await db.execute("""
                UPDATE users
                SET first_name = ?, last_name = ?, username = ?, last_seen = ?, message_count = message_count + 1
                WHERE user_id = ?
            """, (first_name, last_name, username, now, user_id))
            await db.commit()
            return False

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve user information."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_all_users() -> List[Dict[str, Any]]:
    """Retrieve all customers."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY last_seen DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_latest_active_customer() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently active customer."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY last_seen DESC LIMIT 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def set_customer_mode(user_id: int, mode: str):
    """Set customer conversation mode ('ai' or 'manual')."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET chat_mode = ? WHERE user_id = ?", (mode, user_id))
        await db.commit()

async def get_customer_mode(user_id: int) -> str:
    """Get customer conversation mode ('ai' or 'manual'). Defaults to 'ai'."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_mode FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if (row and row[0]) else "ai"

async def set_user_topic_id(user_id: int, topic_id: int):
    """Store forum topic ID for this user."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET topic_id = ? WHERE user_id = ?", (topic_id, user_id))
        await db.commit()

async def get_user_by_topic_id(topic_id: int) -> Optional[Dict[str, Any]]:
    """Find customer by their forum topic thread ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE topic_id = ?", (topic_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def save_message_mapping(admin_message_id: int, customer_chat_id: int, customer_message_id: int):
    """Save forwarded message ID mapping for swipe-to-reply."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO message_mappings (admin_message_id, customer_chat_id, customer_message_id)
            VALUES (?, ?, ?)
        """, (admin_message_id, customer_chat_id, customer_message_id))
        await db.commit()

async def get_message_mapping(admin_message_id: int) -> Optional[Dict[str, int]]:
    """Look up original customer message by forwarded admin message ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT customer_chat_id, customer_message_id 
            FROM message_mappings 
            WHERE admin_message_id = ?
        """, (admin_message_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "customer_chat_id": row[0],
                    "customer_message_id": row[1]
                }
            return None

async def log_message(user_id: int, sender_type: str, text_content: Optional[str]):
    """Log customer or admin message for conversation observation."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO messages (user_id, sender_type, text_content)
            VALUES (?, ?, ?)
        """, (user_id, sender_type, text_content or ""))
        await db.commit()

async def get_user_recent_messages(user_id: int, limit: int = 6) -> List[Dict[str, Any]]:
    """Retrieve recent messages for conversation context."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT sender_type, text_content, created_at 
            FROM messages 
            WHERE user_id = ? 
            ORDER BY id DESC 
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

# -------------------------------------------------------------
# Continuous Learning & Self-Correction Functions
# -------------------------------------------------------------
async def add_learned_correction(guidance: str, topic: str = "General") -> int:
    """Store a new learned correction/rule from Admin feedback."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO learned_corrections (topic, guidance)
            VALUES (?, ?)
        """, (topic, guidance))
        await db.commit()
        return cursor.lastrowid

async def get_all_learned_corrections() -> List[Dict[str, Any]]:
    """Retrieve all learned corrections."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM learned_corrections ORDER BY id DESC
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def delete_learned_correction(correction_id: int) -> bool:
    """Delete a learned correction by ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM learned_corrections WHERE id = ?", (correction_id,))
        await db.commit()
        return cursor.rowcount > 0
