import os
import asyncio
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, ADMIN_CHAT_ID
from database import init_db
from handlers import customer, admin, menu

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("CustomerBot")

async def handle_health(request):
    """Health check endpoint for Render / Cloud hosting."""
    return web.Response(text="InboundSupportBot is running 24/7!", status=200)

async def start_web_server():
    """Starts a minimal background HTTP server to satisfy free cloud hosting requirements."""
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Cloud Health Check Web Server running on port {port}")

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error(
            "❌ TELEGRAM_BOT_TOKEN is missing! Please set it in your .env file."
        )
        print("\n" + "="*50)
        print("⚠️ ACTION REQUIRED:")
        print("1. Open or create the '.env' file in this folder.")
        print("2. Put your Telegram Bot Token from @BotFather in TELEGRAM_BOT_TOKEN.")
        print("3. Put your Chat ID from @userinfobot in ADMIN_CHAT_ID.")
        print("="*50 + "\n")
        return

    # Start Cloud Health Server (Runs alongside Telegram Bot)
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Could not start web server on port: {e}")

    # Initialize SQLite database
    logger.info("Initializing database...")
    await init_db()

    # Initialize Bot & Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register routers in priority order
    dp.include_router(admin.router)
    dp.include_router(menu.router)
    dp.include_router(customer.router)

    # Fetch bot information
    bot_info = await bot.get_me()
    logger.info(f"🚀 Bot started successfully as @{bot_info.username} (ID: {bot_info.id})")
    if ADMIN_CHAT_ID:
        logger.info(f"👑 Admin Chat configured: {ADMIN_CHAT_ID}")
    else:
        logger.warning("⚠️ ADMIN_CHAT_ID is not configured yet! Incoming messages will not be forwarded.")

    # Start polling
    try:
        # Delete any pending webhook updates
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
