import logging
from typing import Dict
from aiogram import Router, Bot, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply
)
from aiogram.filters import Command

from config import ADMIN_CHAT_ID, ADMIN_TOPIC_ID
from database import (
    get_setting,
    set_setting,
    get_all_users,
    get_latest_active_customer,
    get_user,
    get_user_by_topic_id,
    get_message_mapping,
    save_message_mapping,
    set_customer_mode,
    log_message,
    add_learned_correction,
    get_all_learned_corrections,
    delete_learned_correction
)
from services.timer_manager import cancel_pending_timer

router = Router()
logger = logging.getLogger(__name__)

def is_admin_chat(message: Message) -> bool:
    if not ADMIN_CHAT_ID:
        return False
    return message.chat.id == ADMIN_CHAT_ID or (message.from_user and message.from_user.id == ADMIN_CHAT_ID)

def is_admin_callback(callback: CallbackQuery) -> bool:
    if not ADMIN_CHAT_ID:
        return False
    return callback.message.chat.id == ADMIN_CHAT_ID or callback.from_user.id == ADMIN_CHAT_ID

@router.message(Command("id"))
@router.message(Command("topic"))
async def chat_id_helper_handler(message: Message):
    """Helper command to easily find the Chat ID and Topic/Thread ID of any group or topic."""
    chat_id = message.chat.id
    thread_id = message.message_thread_id
    chat_title = message.chat.title or message.chat.full_name or "Private Chat"
    
    topic_str = f"<code>{thread_id}</code>" if thread_id else "<i>None (General / Main Chat)</i>"
    
    text = (
        f"📍 <b>Telegram Location Details:</b>\n\n"
        f"📛 <b>Name:</b> {chat_title}\n"
        f"🆔 <b>Chat / Group ID:</b> <code>{chat_id}</code>\n"
        f"🏷️ <b>Topic / Thread ID:</b> {topic_str}\n\n"
        f"⚙️ <b>Copy to your <code>.env</code> file:</b>\n"
        f"<code>ADMIN_CHAT_ID={chat_id}</code>\n"
    )
    if thread_id:
        text += f"<code>ADMIN_TOPIC_ID={thread_id}</code>\n"
    
    await message.answer(text, parse_mode="HTML")

@router.message(Command("start"), is_admin_chat)
@router.message(Command("help"), is_admin_chat)
async def admin_help_handler(message: Message):
    help_text = (
        "👑 <b>Admin Control Panel (Hybrid AI + Human)</b>\n\n"
        "<b>🤖 Continuous Learning & Self-Correction:</b>\n"
        "• <code>/teach &lt;lesson&gt;</code> - Teach the bot a new rule or correct a past mistake\n"
        "• <code>/learnings</code> - View all active learned lessons/corrections\n"
        "• <code>/forget &lt;id&gt;</code> - Remove a learned lesson\n\n"
        "<b>💬 How to reply to customers:</b>\n"
        "• <b>Quick Takeover:</b> Click <code>[ 👤 Take Over / Reply ]</code> on any customer message to pause AI and chat manually.\n"
        "• <b>Resume Automation:</b> Click <code>[ 🤖 Resume Automation ]</code> whenever you want AI to take back over.\n\n"
        "<b>⚙️ Management Commands:</b>\n"
        "• <code>/id</code> or <code>/topic</code> - Get the current Group ID and Topic/Thread ID\n"
        "• <code>/setreply &lt;text&gt;</code> - Change the fallback welcome message\n"
        "• <code>/getreply</code> - View current default reply & mode\n"
        "• <code>/users</code> - View customer statistics and user list\n"
        "• <code>/send &lt;user_id&gt; &lt;text&gt;</code> - Send direct message to a customer\n"
        "• <code>/broadcast &lt;text&gt;</code> - Broadcast announcement to all customers"
    )
    await message.answer(help_text, parse_mode="HTML")

# -------------------------------------------------------------
# Learning & Correction Commands
# -------------------------------------------------------------
@router.message(Command("teach"), is_admin_chat)
async def teach_bot_handler(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "⚠️ Usage: <code>/teach &lt;rule or correction&gt;</code>\n\n"
            "<b>Example:</b>\n"
            "<code>/teach When customer asks for ABA payment discount, tell them we offer 5% cash discount.</code>",
            parse_mode="HTML"
        )
        return

    guidance = parts[1].strip()
    item_id = await add_learned_correction(guidance=guidance)
    await message.answer(
        f"🧠 <b>Learned New Rule [ID: {item_id}]!</b>\n\n"
        f"✅ <i>\"{guidance}\"</i>\n\n"
        f"The AI will immediately remember this rule and avoid past mistakes when answering customers!",
        parse_mode="HTML"
    )

@router.message(Command("learnings"), is_admin_chat)
@router.message(Command("memories"), is_admin_chat)
async def view_learnings_handler(message: Message):
    items = await get_all_learned_corrections()
    if not items:
        await message.answer("🧠 No custom corrections learned yet. You can teach the bot anytime with <code>/teach &lt;rule&gt;</code>.", parse_mode="HTML")
        return

    lines = []
    for item in items:
        lines.append(f"• <b>[ID: {item['id']}]</b> {item['guidance']} <i>({item['created_at'][:10]})</i>")

    text = f"🧠 <b>Active Learned Corrections ({len(items)}):</b>\n\n" + "\n\n".join(lines) + "\n\n💡 <i>To delete a rule, use <code>/forget &lt;id&gt;</code></i>"
    await message.answer(text, parse_mode="HTML")

@router.message(Command("forget"), is_admin_chat)
async def forget_learning_handler(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ Usage: <code>/forget &lt;id&gt;</code>", parse_mode="HTML")
        return

    try:
        item_id = int(parts[1].strip())
    except ValueError:
        await message.answer("⚠️ Invalid ID. Must be a number.", parse_mode="HTML")
        return

    success = await delete_learned_correction(item_id)
    if success:
        await message.answer(f"🗑️ Learned correction <b>[ID: {item_id}]</b> deleted.", parse_mode="HTML")
    else:
        await message.answer(f"⚠️ Could not find learned correction with ID {item_id}.", parse_mode="HTML")

# -------------------------------------------------------------
# -------------------------------------------------------------
# Dynamic Mode Toggle Callbacks
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("takeover_user_"), is_admin_callback)
@router.callback_query(F.data.startswith("reply_user_"), is_admin_callback)
async def process_takeover_click(callback: CallbackQuery, bot: Bot):
    prefix = "takeover_user_" if callback.data.startswith("takeover_user_") else "reply_user_"
    customer_id_str = callback.data.replace(prefix, "")
    try:
        customer_id = int(customer_id_str)
    except ValueError:
        await callback.answer("⚠️ Invalid customer ID.", show_alert=True)
        return

    cancel_pending_timer(customer_id)
    await set_customer_mode(customer_id, "manual")

    user_info = await get_user(customer_id)
    customer_name = user_info.get("first_name", "Customer") if user_info else "Customer"

    resume_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"🤖 Resume AI for {customer_name}", callback_data=f"resume_auto_{customer_id}")]
        ]
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=resume_keyboard)
    except Exception:
        pass

    await callback.answer(f"⏸️ AI Paused. Swipe to Reply to this card to chat with {customer_name}!", show_alert=True)

@router.callback_query(F.data.startswith("resume_auto_"), is_admin_callback)
async def process_resume_auto_click(callback: CallbackQuery, bot: Bot):
    customer_id_str = callback.data.replace("resume_auto_", "")
    try:
        customer_id = int(customer_id_str)
    except ValueError:
        await callback.answer("⚠️ Invalid customer ID.", show_alert=True)
        return

    await set_customer_mode(customer_id, "ai")

    user_info = await get_user(customer_id)
    customer_name = user_info.get("first_name", "Customer") if user_info else "Customer"

    takeover_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"⏸️ Pause AI for {customer_name}", callback_data=f"takeover_user_{customer_id}")]
        ]
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=takeover_keyboard)
    except Exception:
        pass

    await callback.answer(f"🟢 AI Automation resumed for {customer_name}.")

# -------------------------------------------------------------
# Management Commands
# -------------------------------------------------------------
@router.message(Command("setreply"), is_admin_chat)
async def set_reply_handler(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("⚠️ Usage: <code>/setreply Your fallback message here</code>", parse_mode="HTML")
        return

    new_reply = parts[1].strip()
    await set_setting("auto_reply_text", new_reply)
    await message.answer(f"✅ <b>Fallback auto-reply updated to:</b>\n\n{new_reply}", parse_mode="HTML")

@router.message(Command("getreply"), is_admin_chat)
async def get_reply_handler(message: Message):
    current_reply = await get_setting("auto_reply_text", "No message set.")
    mode = await get_setting("auto_reply_mode", "always")
    await message.answer(
        f"📋 <b>Current Settings:</b>\n\n"
        f"<b>Default Mode:</b> <code>{mode}</code>\n"
        f"<b>Fallback Greeting:</b>\n{current_reply}",
        parse_mode="HTML"
    )

@router.message(Command("users"), is_admin_chat)
@router.message(Command("stats"), is_admin_chat)
async def list_users_handler(message: Message):
    users = await get_all_users()
    if not users:
        await message.answer("📊 No customers have contacted the bot yet.")
        return

    user_lines = []
    for idx, u in enumerate(users[:20], 1):
        username = f"@{u['username']}" if u.get("username") else "No username"
        mode_icon = "🟢 AI" if u.get("chat_mode", "ai") == "ai" else "🟠 Manual"
        user_lines.append(f"{idx}. <b>{u['first_name']}</b> ({username}) | ID: <code>{u['user_id']}</code> | [{mode_icon}]")

    total = len(users)
    text = f"📊 <b>Total Customers:</b> {total}\n\n" + "\n".join(user_lines)
    if total > 20:
        text += f"\n\n<i>...and {total - 20} more.</i>"

    await message.answer(text, parse_mode="HTML")

@router.message(Command("send"), is_admin_chat)
async def send_to_user_handler(message: Message, bot: Bot):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("⚠️ Usage: <code>/send &lt;user_id&gt; &lt;message&gt;</code>", parse_mode="HTML")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("⚠️ Invalid user ID. It must be a number.", parse_mode="HTML")
        return

    msg_to_send = parts[2]
    try:
        cancel_pending_timer(target_id)
        await bot.send_message(chat_id=target_id, text=msg_to_send)
        await log_message(target_id, "admin", msg_to_send)
        await message.answer(f"✅ Message delivered to user <code>{target_id}</code>.", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Failed to send message: {e}")

@router.message(Command("broadcast"), is_admin_chat)
async def broadcast_handler(message: Message, bot: Bot):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer("⚠️ Usage: <code>/broadcast Your message here</code>", parse_mode="HTML")
        return

    broadcast_text = parts[1].strip()
    users = await get_all_users()
    if not users:
        await message.answer("No customers to broadcast to.")
        return

    status_msg = await message.answer(f"🚀 Broadcasting to {len(users)} users...")
    success, failed = 0, 0

    for u in users:
        try:
            await bot.send_message(chat_id=u["user_id"], text=broadcast_text)
            success += 1
        except Exception:
            failed += 1

    await status_msg.edit_text(
        f"📢 <b>Broadcast Complete!</b>\n"
        f"✅ Sent: {success}\n"
        f"❌ Failed (blocked/deleted): {failed}",
        parse_mode="HTML"
    )

# -------------------------------------------------------------
# Core Relay Handler: Delivering Admin's Reply to the Customer
# -------------------------------------------------------------
@router.message(is_admin_chat)
async def handle_admin_reply(message: Message, bot: Bot):
    # Ignore commands
    if message.text and message.text.startswith("/"):
        return

    customer_id = None

    # Priority 1: Direct Reply to a specific customer notification card in Telegram
    if message.reply_to_message:
        mapping = await get_message_mapping(message.reply_to_message.message_id)
        if mapping:
            customer_id = mapping["customer_chat_id"]

    # Priority 2: Message typed directly inside the dedicated Support Topic (Topic 11379)
    is_in_support_topic = bool(ADMIN_TOPIC_ID and message.message_thread_id == ADMIN_TOPIC_ID)
    if not customer_id and is_in_support_topic:
        latest_user = await get_latest_active_customer()
        if latest_user:
            customer_id = latest_user["user_id"]

    # Priority 3: Dynamic Per-Customer Topic Mode
    if not customer_id and message.message_thread_id:
        user_data = await get_user_by_topic_id(message.message_thread_id)
        if user_data:
            customer_id = user_data["user_id"]

    # If message is in General or other topics and NOT a reply to a customer, IGNORE completely!
    if not customer_id:
        return

    try:
        cancel_pending_timer(customer_id)

        # Forward / copy admin's reply to customer
        await message.copy_to(chat_id=customer_id)
        await log_message(customer_id, "admin", message.text or message.caption or "[Media/Attachment]")
        
        user_info = await get_user(customer_id)
        name = user_info.get("first_name", "Customer") if user_info else "Customer"
        
        thread_id = message.message_thread_id or ADMIN_TOPIC_ID or None
        kwargs = {
            "chat_id": message.chat.id,
            "text": f"✅ <i>Delivered to {name}</i>",
            "parse_mode": "HTML",
            "reply_to_message_id": message.message_id
        }
        if thread_id:
            kwargs["message_thread_id"] = thread_id
        await bot.send_message(**kwargs)
    except Exception as e:
        logger.error(f"Failed to deliver admin reply to customer {customer_id}: {e}")


