import logging
from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_CHAT_ID, ADMIN_TOPIC_ID, ADMIN_REPLY_TIMEOUT_SECONDS
from database import log_message, save_message_mapping, get_customer_mode

router = Router()
logger = logging.getLogger(__name__)

def get_faq_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns the interactive main menu keyboard for Camera Surveillance System Information."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 របៀបដំណើរការប្រព័ន្ធ (How It Works / Workflow)",
                    callback_data="faq_workflow"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📹 ការភ្ជាប់កាមេរ៉ា & RTSP (Compatibility)",
                    callback_data="faq_cameras"
                ),
                InlineKeyboardButton(
                    text="🧠 សមត្ថភាព & មុខងារ AI (AI Features)",
                    callback_data="faq_features"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛡️ សុវត្ថិភាព & Local Edge (Privacy)",
                    callback_data="faq_architecture"
                ),
                InlineKeyboardButton(
                    text="📲 ការដាស់តឿន & Dashboard (Alerts)",
                    callback_data="faq_alerts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 សួរសំណួរបន្ថែម (Ask System Question)",
                    callback_data="faq_custom"
                )
            ]
        ]
    )

def get_sub_menu_keyboard() -> InlineKeyboardMarkup:
    """Returns navigation keyboard for sub-views with back button and quick ask."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ ត្រឡប់ទៅម៉ឺនុយដើម (Main Menu)",
                    callback_data="faq_main_menu"
                ),
                InlineKeyboardButton(
                    text="💬 សួរសំណួរ (Ask Question)",
                    callback_data="faq_custom"
                )
            ]
        ]
    )

# -------------------------------------------------------------
# Main Menu Handler
# -------------------------------------------------------------
@router.callback_query(F.data == "faq_main_menu")
async def faq_main_menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "🏢 <b>ព័ត៌មានលម្អិតអំពីប្រព័ន្ធកាមេរ៉ាសុវត្ថិភាព AI (AI Camera Surveillance System)</b>\n\n"
        "សូមជ្រើសរើសប្រធានបទខាងក្រោមដើម្បីស្វែងយល់បន្ថែមអំពីដំណើរការ មុខងារ និងស្ថាបត្យកម្មបច្ចេកវិទ្យារបស់ប្រព័ន្ធ:\n\n"
        "👇 <i>ចុចលើប៊ូតុងខាងក្រោម ឬសរសេរសំណួរដោយផ្ទាល់:</i>"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_faq_menu_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_faq_menu_keyboard())
    await log_message(user_id, "customer", "[Clicked: Main Menu]")
    await callback.answer()

# -------------------------------------------------------------
# System Information & Workflow FAQ Handlers
# -------------------------------------------------------------

@router.callback_query(F.data == "faq_workflow")
async def faq_workflow_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "🔄 <b>លំហូរការងារ និងដំណើរការនៃប្រព័ន្ធ (System Workflow & Pipeline):</b>\n\n"
        "ប្រព័ន្ធដំណើរការតាម ៤ ដំណាក់កាលបន្តបន្ទាប់គ្នា (End-to-End Pipeline):\n\n"
        "1. 📥 <b>Video Ingestion (ការទាញយកវីដេអូ):</b>\n"
        "• ទាញយកខ្សែវីដេអូ Real-Time ពីកាមេរ៉ាសុវត្ថិភាព (IP / CCTV) តាមរយៈ RTSP/ONVIF Protocol ក្នុងបណ្តាញ Local Network។\n\n"
        "2. 🧠 <b>Edge AI Inference (ការវិភាគដោយ AI):</b>\n"
        "• ម៉ាស៊ីន AI (Neural Network Model) វិភាគមនុស្ស យានយន្ត ចលនា និងសកម្មភាពក្នុងកម្រិតល្បឿន Real-Time។\n"
        "• តាមដានគន្លងផ្លូវ (Multi-Object Tracking) របស់មនុស្ស និងយានយន្តនីមួយៗ។\n\n"
        "3. 📐 <b>Spatial Zone & Rule Engine (ការផ្ទៀងផ្ទាត់តំបន់ & ច្បាប់):</b>\n"
        "• ពិនិត្យព្រឹត្តិការណ៍តាមតំបន់កំណត់ (ROI Polygons) ដូចជា តំបន់ហាមឃាត់, រយៈពេលឈររង់ចាំ (Dwell Time), និងអវត្តមានបុគ្គលិក។\n\n"
        "4. 📲 <b>Alert & Dashboard Dispatch (ការដាស់តឿន & បង្ហាញទិន្នន័យ):</b>\n"
        "• ផ្ញើសារ Alert ភ្លាមៗ (< 2 វិនាទី) ជាមួយរូបថតភស្តុតាងចូល Telegram របស់អ្នកគ្រប់គ្រង និងបង្ហាញលើ Live Dashboard។"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    await log_message(user_id, "customer", "[Clicked: FAQ Workflow]")
    await log_message(user_id, "bot", text)
    await callback.answer()

@router.callback_query(F.data == "faq_cameras")
async def faq_cameras_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "📹 <b>ការភ្ជាប់កាមេរ៉ា & ភាពត្រូវគ្នា (Camera Compatibility & Protocols):</b>\n\n"
        "• <b>ពិធីការដែលគាំទ្រ (Supported Protocols):</b>\n"
        "  - RTSP (Real-Time Streaming Protocol)\n"
        "  - ONVIF (Profile S / G / T)\n"
        "  - HTTP / WebRTC Streams & Local USB Webcams\n\n"
        "• <b>ម៉ាកកាមេរ៉ាដែលប្រើបាន (Supported Brands):</b>\n"
        "  - Hikvision, Dahua, Uniview (UNV), Tiandy\n"
        "  - TP-Link Tapo, Ezviz, Imou, Reolink\n"
        "  - គ្រប់កាមេរ៉ា IP Camera, NVR ឬ DVR ទាំងអស់ដែលមានមុខងារ RTSP/ONVIF។\n\n"
        "• <b>ការតភ្ជាប់បណ្តាញ (Network Setup):</b>\n"
        "  - ដំណើរការលើបណ្តាញ Local Area Network (LAN/Wi-Fi) តែមួយ មិនចាំបាច់មាន Public Static IP ឡើយ។"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    await log_message(user_id, "customer", "[Clicked: FAQ Cameras & Compatibility]")
    await log_message(user_id, "bot", text)
    await callback.answer()

@router.callback_query(F.data == "faq_features")
async def faq_features_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "🧠 <b>សមត្ថភាព និងមុខងារ AI សំខាន់ៗ (Core AI Vision Capabilities):</b>\n\n"
        "1. 👥 <b>Human & Presence Detection:</b>\n"
        "• កំណត់អត្តសញ្ញាណមនុស្ស ចំនួនមនុស្ស និងវត្តមានក្នុងតំបន់នីមួយៗ (Face ID + Local Network Verification)។\n\n"
        "2. 🚗 <b>Vehicle & Asset Tracking:</b>\n"
        "• ចាប់រថយន្ត ម៉ូតូ និងវាស់ស្ទង់រយៈពេលចត/ជួសជុលក្នុងតំបន់ជាក់លាក់ (Bay / Parking Tracking)។\n\n"
        "3. 🛑 <b>Restricted Area & Intrusion Alert:</b>\n"
        "• បង្កើតបន្ទាត់ព្រំដែននិម្មិត (Virtual Fence) និងដាស់តឿនភ្លាមៗពេលមានមនុស្សចូលតំបន់ហាមឃាត់។\n\n"
        "4. ⏱️ <b>Dwell Time & Loitering Monitoring:</b>\n"
        "• វាស់ស្ទង់រយៈពេលនៃការឈររង់ចាំ និងដាស់តឿនពេលមានការប្រមូលផ្តុំយូរខុសប្រក្រតី។\n\n"
        "5. ⚠️ <b>Station Absence Detection:</b>\n"
        "• ដាស់តឿនភ្លាមៗពេលកន្លែងប្រចាំការសំខាន់ៗ (ដូចជា បញ្ជរគិតលុយ ឬតុទទួលភ្ញៀវ) គ្មានវត្តមានបុគ្គលិកឈរ។"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    await log_message(user_id, "customer", "[Clicked: FAQ AI Features]")
    await log_message(user_id, "bot", text)
    await callback.answer()

@router.callback_query(F.data == "faq_architecture")
async def faq_architecture_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "🛡️ <b>ស្ថាបត្យកម្មប្រព័ន្ធ និងសុវត្ថិភាពទិន្នន័យ (Architecture & Privacy):</b>\n\n"
        "• <b>100% On-Premise / Edge Computing:</b>\n"
        "  - ការវិភាគវីដេអូទាំងអស់ត្រូវបានដំណើរការលើកុំព្យូទ័រ Edge ក្នុងអាគារផ្ទាល់ មិនបញ្ជូនខ្សែវីដេអូចេញក្រៅឡើយ។\n"
        "  - រក្សាការសម្ងាត់ និងសុវត្ថិភាពទិន្នន័យបាន ១០០% (100% Data Privacy)។\n\n"
        "• <b>Zero Bandwidth Congestion:</b>\n"
        "  - មិនស៊ីល្បឿនអ៊ីនធឺណិតក្នុងការ Upload វីដេអូទៅកាន់ Cloud ឡើយ។\n\n"
        "• <b>Hardware Recommendations (តម្រូវការផ្នែករឹង):</b>\n"
        "  - CPU: Intel Core i5/i7 (Gen 8+) ឬ AMD Ryzen 5/7\n"
        "  - RAM: 8GB – 16GB\n"
        "  - GPU (Optional for multiple streams): NVIDIA GTX/RTX គាំទ្រ CUDA Acceleration។\n"
        "  - OS: Windows 10/11 ឬ Linux (Ubuntu/Debian)។"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    await log_message(user_id, "customer", "[Clicked: FAQ Architecture & Privacy]")
    await log_message(user_id, "bot", text)
    await callback.answer()

@router.callback_query(F.data == "faq_alerts")
async def faq_alerts_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    text = (
        "📲 <b>ការដាស់តឿន Alert & Dashboard (Alerts & Monitoring Integration):</b>\n\n"
        "• <b>Instant Telegram Alert:</b>\n"
        "  - ផ្ញើសារដាស់តឿនភ្លាមៗ (< 2 វិនាទី) ទៅកាន់ Telegram របស់អ្នកគ្រប់គ្រង ភ្ជាប់ជាមួយរូបភាព Snapshot ភស្តុតាង និង Timestamp ជាក់ស្តែង។\n\n"
        "• <b>Real-Time Live HUD Dashboard:</b>\n"
        "  - ផ្ទាំងបញ្ជាបន្តផ្ទាល់តាមរយៈ WebRTC HUD សម្រាប់ត្រួតពិនិត្យស្ថានភាពកាមេរ៉ាទាំងអស់ ចលនានៅក្នុងតំបន់ (Zones) និងប្រវត្តិនៃការឆ្លងកាត់។\n\n"
        "• <b>Customizable Trigger Rules:</b>\n"
        "  - អាចកំណត់លក្ខខណ្ឌដាស់តឿនតាមពេលវេលា (ឧ. ម៉ោងធ្វើការ / ក្រៅម៉ោងធ្វើការ) និងតាមកម្រិតសំខាន់នៃតំបន់នីមួយៗ។\n\n"
        "• <b>Event History & Database Logs:</b>\n"
        "  - រាល់ព្រឹត្តិការណ៍ទាំងអស់ត្រូវបានរក្សាទុកក្នុង Local Database សម្រាប់ទាញយករបាយការណ៍ និងស្ថិតិ។"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    await log_message(user_id, "customer", "[Clicked: FAQ Alerts & Dashboard]")
    await log_message(user_id, "bot", text)
    await callback.answer()

# -------------------------------------------------------------
# Custom Question Click (ALERTS the Admin & Prompts Customer)
# -------------------------------------------------------------
@router.callback_query(F.data == "faq_custom")
async def faq_custom_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    user_id = user.id

    text = (
        "✍️ <b>សូមសរសេរសំណួរអំពីប្រព័ន្ធរបស់លោកអ្នកនៅទីនេះ:</b>\n\n"
        "<i>លោកអ្នកអាចសួរអំពី ស្ថាបត្យកម្មប្រព័ន្ធ (Architecture), ពិធីការ RTSP, មុខងារ AI, ការវិភាគរូបភាព, ឬលំហូរការងារ (System Workflow) ផ្សេងៗ។ ប្រព័ន្ធនឹងឆ្លើយតបជូនភ្លាមៗបាទ/ចាស!</i>"
    )
    try:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=get_sub_menu_keyboard())
    except Exception:
        pass
    await log_message(user_id, "customer", "[Clicked: 💬 សួរសំណួរបន្ថែម]")
    await callback.answer()

    if not ADMIN_CHAT_ID:
        return

    current_mode = await get_customer_mode(user_id)
    username_str = f" (@{user.username})" if user.username else ""

    if current_mode == "ai":
        status_badge = f"⏳ <b>Waiting for Admin</b> (AI auto-answers in {ADMIN_REPLY_TIMEOUT_SECONDS}s)"
        button_text = f"⏸️ Pause AI for {user.first_name}"
        button_callback = f"takeover_user_{user_id}"
    else:
        status_badge = "🟠 <b>Manual Human Mode (AI Paused)</b>"
        button_text = f"🤖 Resume AI for {user.first_name}"
        button_callback = f"resume_auto_{user_id}"

    admin_header = (
        f"📩 <b>Customer Wants to Ask a Question:</b>\n"
        f"👤 <b>{user.full_name}</b>{username_str} <code>[ID: {user_id}]</code>\n"
        f"📡 <b>Status:</b> {status_badge}\n"
        f"🧠 <b>Action:</b> Clicked [💬 សួរសំណួរបន្ថែម / Ask System Question]\n\n"
        f"<i>💡 To reply, simply swipe/reply directly to this message.</i>"
    )

    action_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data=button_callback)]
        ]
    )

    try:
        kwargs = {"chat_id": ADMIN_CHAT_ID, "text": admin_header, "reply_markup": action_keyboard, "parse_mode": "HTML"}
        if ADMIN_TOPIC_ID:
            kwargs["message_thread_id"] = ADMIN_TOPIC_ID
        notif = await bot.send_message(**kwargs)
        await save_message_mapping(notif.message_id, user_id, 0)
    except Exception as e:
        logger.error(f"Error alerting admin of custom question request: {e}")
