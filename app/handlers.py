from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 ¡Hola! Soy FinIntelBot.\n\n"
        "• Usa /id en cualquier chat para obtener el ID y añadirlo a TELEGRAM_TARGETS.\n"
        "• Envío de noticias (RSS) + señales técnicas US30 (yfinance)."
    )
    await update.message.reply_text(text)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Comandos:\n"
        "/start - Mensaje de bienvenida\n"
        "/help  - Ayuda\n"
        "/id    - Devuelve el ID del chat actual"
    )
    await update.message.reply_text(text)

async def chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    await update.message.reply_text(f"El ID de este chat es: <code>{cid}</code>", parse_mode="HTML")
