# 🤖 Telegram Customer Support & Reply Bot

A lightweight, seamless Telegram bot that:
- Automatically greets and answers your customers with your custom message upon contact.
- Seamlessly mirrors incoming customer messages (text, photos, voices, documents, stickers) to your personal Telegram chat or private forum group.
- Lets you **reply to customers whenever you are free** by simply swiping and clicking **Reply** in Telegram (or typing directly inside their topic tab).
- Leaves customers completely unaware whether they are chatting with an automated response or a live person.

---

## 🚀 Quick Setup Guide

### Step 1: Get your Bot Token & Chat ID
1. **Telegram Bot Token**:
   - Message [@BotFather](https://t.me/BotFather) on Telegram and create a bot (`/newbot`).
   - Copy the HTTP API token (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).
2. **Your Admin Chat ID**:
   - Message [@userinfobot](https://t.me/userinfobot) on Telegram and copy your numeric `Id` (e.g., `987654321`).

---

### Step 2: Configure `.env`
Create a `.env` file in this folder (or copy from `.env.example`):
```bash
cp .env.example .env
```
Open `.env` and fill in your details:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
ADMIN_CHAT_ID=987654321
DEFAULT_AUTO_REPLY="Hello! Thank you for reaching out. We have received your message and will get back to you shortly."
AUTO_REPLY_MODE=first_time
```

---

### Step 3: Run the Bot
```bash
./venv/bin/python bot.py
```

---

## 💬 How to Chat with Customers

### Method 1: In Direct Chat (Swipe to Reply)
1. When a customer messages the bot, you receive a notification in your private Telegram chat with the customer's name and message.
2. In your Telegram app, **swipe right / click "Reply"** on the customer's message.
3. Type your answer (or send voice/photo) and press **Send**.
4. The bot immediately sends it directly to that customer!

### Method 2: Forum Topics (Like Individual Friend Chats)
1. Create a private Telegram group with only **You and your Bot**.
2. Go to Group Settings and enable **Topics**.
3. Set `ADMIN_CHAT_ID` to your Group ID (e.g. `-100xxxxxxxxx`).
4. The bot will automatically create a **new topic tab for each customer** with their name. You can just open their tab and chat naturally!

---

## 👑 Admin Commands

You can send these commands directly to the bot from your admin account:
- `/setreply <text>` - Change the automated reply message anytime.
- `/getreply` - View the current automated reply and mode.
- `/autoreply <first_time|always|disabled>` - Set when auto-reply triggers.
- `/users` - View customer statistics and list of all contacts.
- `/broadcast <text>` - Send an announcement message to all customers.
- `/send <user_id> <text>` - Send a direct message to a specific customer ID.
