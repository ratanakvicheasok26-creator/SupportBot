import asyncio
import logging
from typing import Dict
from aiogram import Bot
from config import ADMIN_REPLY_TIMEOUT_SECONDS, ADMIN_CHAT_ID, ADMIN_TOPIC_ID
from database import get_customer_mode, get_user_recent_messages, log_message
from services.ai_assistant import generate_ai_response

logger = logging.getLogger(__name__)

# Dictionary tracking pending AI timer tasks: { user_id: asyncio.Task }
pending_ai_timers: Dict[int, asyncio.Task] = {}

def cancel_pending_timer(user_id: int) -> bool:
    """Cancels any pending AI auto-reply timer for this user."""
    if user_id in pending_ai_timers:
        task = pending_ai_timers[user_id]
        if not task.done():
            task.cancel()
            logger.info(f"Pending AI timer cancelled for user {user_id} (Admin took action).")
        del pending_ai_timers[user_id]
        return True
    return False

async def delayed_ai_worker(
    bot: Bot,
    user_id: int,
    customer_name: str,
    message_text: str,
    admin_notif_msg_id: int = None
):
    """
    Waits for ADMIN_REPLY_TIMEOUT_SECONDS (1 minute).
    If Admin does not reply within this window, AI auto-replies.
    """
    try:
        await asyncio.sleep(ADMIN_REPLY_TIMEOUT_SECONDS)
        
        # Check if customer mode is still 'ai' (not manually taken over)
        mode = await get_customer_mode(user_id)
        if mode != "ai":
            logger.info(f"User {user_id} is in manual mode. AI timer skipping response.")
            return

        # Generate AI response
        recent_history = await get_user_recent_messages(user_id, limit=6)
        ai_reply = await generate_ai_response(
            customer_name=customer_name,
            message_text=message_text,
            recent_history=recent_history
        )

        if ai_reply:
            # Deliver AI answer to customer
            await bot.send_message(chat_id=user_id, text=ai_reply)
            await log_message(user_id, "bot", ai_reply)

            # Inform Admin that 1 min timeout passed and AI answered
            if ADMIN_CHAT_ID:
                try:
                    kwargs = {
                        "chat_id": ADMIN_CHAT_ID,
                        "text": (
                            f"🤖 <b>[1 min timeout reached]</b>\n"
                            f"AI auto-replied to <b>{customer_name}</b> (<code>{user_id}</code>):\n\n"
                            f"<i>\"{ai_reply}\"</i>"
                        ),
                        "parse_mode": "HTML"
                    }
                    if ADMIN_TOPIC_ID:
                        kwargs["message_thread_id"] = ADMIN_TOPIC_ID
                    await bot.send_message(**kwargs)
                except Exception as e:
                    logger.error(f"Failed to send timer log to admin: {e}")

    except asyncio.CancelledError:
        logger.info(f"AI timer for user {user_id} was successfully cancelled.")
    except Exception as e:
        logger.error(f"Error in delayed AI worker for user {user_id}: {e}")
    finally:
        if user_id in pending_ai_timers and pending_ai_timers[user_id] == asyncio.current_task():
            del pending_ai_timers[user_id]

def schedule_ai_timer(
    bot: Bot,
    user_id: int,
    customer_name: str,
    message_text: str,
    admin_notif_msg_id: int = None
):
    """Schedules a new AI timer for a customer inquiry."""
    cancel_pending_timer(user_id)
    task = asyncio.create_task(
        delayed_ai_worker(bot, user_id, customer_name, message_text, admin_notif_msg_id)
    )
    pending_ai_timers[user_id] = task
