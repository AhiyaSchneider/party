import os
import json
import pandas as pd
import qrcode
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Load bot token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = -1002253157550  # Replace with your group chat ID

os.makedirs("qrcodes", exist_ok=True)
GUESTS_FILE = "guests.json"

def load_guest_list():
    if os.path.exists(GUESTS_FILE):
        with open(GUESTS_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def save_guest_list(data):
    with open(GUESTS_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

async def generate_qr(name):
    guests = load_guest_list()
    if name in guests:
        return guests[name]["qr_file"]

    qr_data = f"Guest: {name}"
    qr_code = qrcode.make(qr_data)
    qr_filename = f"qrcodes/{name.replace(' ', '_')}.png"
    qr_code.save(qr_filename)

    guests[name] = {"qr_file": qr_filename, "checked_in": False}
    save_guest_list(guests)
    return qr_filename

async def save_guest_to_group(name):
    message = f"📝 Guest Added: {name} | Status: Not Checked In"
    await app.bot.send_message(chat_id=GROUP_ID, text=message)

async def start(update: Update, context: CallbackContext):
    keyboard = [[KeyboardButton("➕ Add Guest")], [KeyboardButton("📋 Show Guests")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome to Guest Manager!", reply_markup=reply_markup)

async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.strip()

    if text == "➕ Add Guest":
        await update.message.reply_text("✍️ Enter guest name:")
        context.user_data["awaiting_name"] = True
    elif text == "📋 Show Guests":
        guests = load_guest_list()
        if not guests:
            await update.message.reply_text("No guests found.")
        else:
            guest_list = "\n".join(
                [f"{name} - {'✅ Checked In' if data['checked_in'] else '❌ Not Checked In'}" for name, data in
                 guests.items()])
            await update.message.reply_text(f"Guest List:\n{guest_list}")
    elif context.user_data.get("awaiting_name"):
        context.user_data["awaiting_name"] = False
        qr_file = await generate_qr(text)
        await update.message.reply_text(f"✅ {text} added! Here is the QR Code.")
        with open(qr_file, "rb") as photo:
            await update.message.reply_photo(photo=photo)
        await save_guest_to_group(text)
    else:
        await update.message.reply_text("❌ Invalid option.")

app = Application.builder().token(TOKEN).build()

# Detect if running on Render and adjust mode accordingly
if "PORT" in os.environ:  # Render requires a port
    PORT = int(os.getenv("PORT", 8443))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"https://api.render.com/deploy/srv-cuovqktsvqrc73et5dmg?key=CgqgW44sz1c"  # Replace with your actual Render URL
    )
else:
    app.run_polling()

print("✅ Bot is running...")
