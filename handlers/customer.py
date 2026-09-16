import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_CHAT_ID, ADMIN_TOPIC_ID, ADMIN_REPLY_TIMEOUT_SECONDS
from database import (
    upsert_user,
    get_user,
    set_user_topic_id,
    save_message_mapping,
    get_customer_mode,
    log_message
)
from observer import analyze_customer_message
from handlers.menu import get_faq_menu_keyboard
from services.timer_manager import schedule_ai_timer

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"), F.chat.type == "private")
async def handle_customer_start(message: Message, bot: Bot):
    user = message.from_user
    if not user or user.id == ADMIN_CHAT_ID:
        return

    await upsert_user(
        user_id=user.id,
        first_name=user.first_name or "Unknown",
        last_name=user.last_name,
        username=user.username
    )

    welcome_text = (
        f"សួស្តីបង <b>{user.first_name}</b>! 👋\n\n"
        "សូមស្វាគមន៍មកកាន់ប្រព័ន្ធព័ត៌មានបច្ចេកវិទ្យា <b>AI Camera Surveillance Platform</b> 📹🧠\n"
        "✨ <i>ស្វែងយល់អំពីដំណើរការ ស្ថាបត្យកម្ម Edge AI, ការភ្ជាប់កាមេរ៉ា RTSP និងមុខងារវិភាគវីដេអូ Real-Time</i>\n\n"
        "👇 <i>លោកអ្នកអាចចុចលើប្រធានបទខាងក្រោម ឬសរសេរសំណួរអំពីប្រព័ន្ធដោយផ្ទាល់:</i>"
    )

    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_faq_menu_keyboard())
    await log_message(user.id, "bot", welcome_text)

    # Notify Admin topic of new customer start
    if ADMIN_CHAT_ID:
        username_str = f" (@{user.username})" if user.username else ""
        button_text = f"👤 Take Over / Reply to {user.first_name}"
        button_callback = f"takeover_user_{user.id}"
        reply_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=button_text, callback_data=button_callback)]
            ]
        )
        start_header = (
            f"🚀 <b>New Customer Started the Bot:</b>\n"
            f"👤 <b>{user.full_name}</b>{username_str} <code>[ID: {user.id}]</code>\n"
            f"📡 <b>Status:</b> 🟢 <i>Customer viewing Welcome FAQ menu</i>"
        )
        kwargs = {
            "chat_id": ADMIN_CHAT_ID,
            "text": start_header,
            "reply_markup": reply_keyboard,
            "parse_mode": "HTML"
        }
        if ADMIN_TOPIC_ID:
            kwargs["message_thread_id"] = ADMIN_TOPIC_ID
        try:
            notif = await bot.send_message(**kwargs)
            await save_message_mapping(notif.message_id, user.id, message.message_id)
        except Exception as e:
            logger.error(f"Error alerting admin topic of customer start: {e}")

@router.message(F.chat.type == "private")
async def handle_customer_message(message: Message, bot: Bot):
    user = message.from_user
    if not user:
        return

    # If message is from the admin in private chat, pass it (handled in admin router)
    if user.id == ADMIN_CHAT_ID:
        return

    text_content = message.text or message.caption or ""

    # 1. Log incoming message to database
    await log_message(user.id, "customer", text_content or "[Media/Attachment]")

    # 2. Upsert customer in database
    await upsert_user(
        user_id=user.id,
        first_name=user.first_name or "Unknown",
        last_name=user.last_name,
        username=user.username
    )

    user_data = await get_user(user.id)
    msg_count = user_data.get("message_count", 1) if user_data else 1
    current_mode = await get_customer_mode(user.id)

    # 3. Schedule 1-minute AI Fallback Timer if in 'ai' mode
    if current_mode == "ai" and text_content:
        schedule_ai_timer(
            bot=bot,
            user_id=user.id,
            customer_name=user.first_name or "Customer",
            message_text=text_content
        )

    # If admin chat is not configured, exit early
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID is not set. Incoming message not forwarded.")
        return

    # 4. Observe customer intent, urgency, and topic
    observation = analyze_customer_message(text_content)

    # 5. Format detailed admin notification header
    username_str = f" (@{user.username})" if user.username else ""
    if current_mode == "ai":
        mode_badge = f"⏳ <b>Waiting for Admin</b> (AI auto-answers in {ADMIN_REPLY_TIMEOUT_SECONDS}s)"
    else:
        mode_badge = "🟠 <b>Manual Human Mode (AI Paused)</b>"
    
    header_lines = [
        f"📩 <b>Incoming Customer Message:</b>",
        f"👤 <b>{user.full_name}</b>{username_str} <code>[ID: {user.id}]</code>",
        f"📡 <b>Status:</b> {mode_badge}",
        f"🧠 <b>Topic:</b> {observation['topic']} | <b>Priority:</b> {observation['urgency']}"
    ]
    if text_content:
        header_lines.append(f"\n💬 <b>Message:</b>\n<i>\"{text_content}\"</i>")

    header_lines.append(f"\n<i>💡 Swipe to Reply to this message to chat with {user.first_name}.</i>")
    user_header = "\n".join(header_lines)

    # 6. Build dynamic Action Button for Admin
    if current_mode == "ai":
        button_text = f"⏸️ Pause AI for {user.first_name}"
        button_callback = f"takeover_user_{user.id}"
    else:
        button_text = f"🤖 Resume AI for {user.first_name}"
        button_callback = f"resume_auto_{user.id}"

    reply_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data=button_callback)]
        ]
    )

    # Check if ADMIN_CHAT_ID is a supergroup with forum topics
    is_supergroup = str(ADMIN_CHAT_ID).startswith("-100")

    if is_supergroup:
        if ADMIN_TOPIC_ID:
            # Dedicated Single Topic Mode
            try:
                notif = await bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    message_thread_id=ADMIN_TOPIC_ID,
                    text=user_header,
                    reply_markup=reply_keyboard,
                    parse_mode="HTML"
                )
                await save_message_mapping(notif.message_id, user.id, message.message_id)

                # Only attempt copy if it's media (photo, voice, document, etc.)
                if not message.text:
                    try:
                        forwarded = await message.copy_to(
                            chat_id=ADMIN_CHAT_ID,
                            message_thread_id=ADMIN_TOPIC_ID
                        )
                        await save_message_mapping(forwarded.message_id, user.id, message.message_id)
                    except Exception as e:
                        logger.warning(f"Could not copy media message: {e}")
            except Exception as e:
                logger.error(f"Error forwarding message to dedicated topic {ADMIN_TOPIC_ID} in {ADMIN_CHAT_ID}: {e}")

        else:
            # 2. Dynamic Per-Customer Topic Mode
            topic_id = user_data.get("topic_id") if user_data else None

            if not topic_id:
                try:
                    topic_name = f"{user.first_name} ({user.id})"
                    topic = await bot.create_forum_topic(chat_id=ADMIN_CHAT_ID, name=topic_name)
                    topic_id = topic.message_thread_id
                    await set_user_topic_id(user.id, topic_id)
                    
                    await bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        message_thread_id=topic_id,
                        text=f"✨ <b>New Customer Thread Opened</b>\n{user_header}",
                        reply_markup=reply_keyboard,
                        parse_mode="HTML"
                    )
                except TelegramBadRequest as e:
                    logger.warning(f"Could not create forum topic: {e}")
                    topic_id = None

            try:
                if topic_id:
                    await bot.send_message(
                        chat_id=ADMIN_CHAT_ID,
                        message_thread_id=topic_id,
                        text=f"🔍 <i>Topic: {observation['topic']}</i>",
                        parse_mode="HTML"
                    )
                    await message.copy_to(
                        chat_id=ADMIN_CHAT_ID,
                        message_thread_id=topic_id
                    )
                else:
                    notif = await bot.send_message(chat_id=ADMIN_CHAT_ID, text=user_header, reply_markup=reply_keyboard, parse_mode="HTML")
                    await save_message_mapping(notif.message_id, user.id, message.message_id)
                    forwarded = await message.copy_to(chat_id=ADMIN_CHAT_ID)
                    await save_message_mapping(forwarded.message_id, user.id, message.message_id)
            except Exception as e:
                logger.error(f"Error forwarding message to group {ADMIN_CHAT_ID}: {e}")

    else:
        # Direct Admin Private Chat Mode
        try:
            notif = await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=user_header,
                reply_markup=reply_keyboard,
                parse_mode="HTML"
            )
            # Map notification card message ID
            await save_message_mapping(notif.message_id, user.id, message.message_id)

            # Copy customer message
            forwarded = await message.copy_to(chat_id=ADMIN_CHAT_ID)
            # Map forwarded customer message ID
            await save_message_mapping(forwarded.message_id, user.id, message.message_id)
        except Exception as e:
            logger.error(f"Error forwarding message to admin {ADMIN_CHAT_ID}: {e}")
