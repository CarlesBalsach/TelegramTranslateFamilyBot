# Simple Telegram translation bot using python-telegram-bot and googletrans.
# It auto-detects messages and translates English to Russian or vice versa.

import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import nest_asyncio  # Allow nested event loops
from openai import OpenAI
from dotenv import load_dotenv
import emoji

nest_asyncio.apply()  # Apply nest_asyncio to fix "event loop already running" issues

# Load environment variables
load_dotenv(dotenv_path=".env")
BOT_TOKEN = os.getenv("TELEGRAM_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = -1003537681211
client = OpenAI(api_key=OPENAI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command. Only responds if the message is from the allowed chat.
    """
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    await update.message.reply_text(
        "Hi there! Send me a message and I'll translate from English/Russian.\n\nПривет, там! Отправьте мне сообщение, и я переведу с английского/русского"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Echo handler (currently not used, but kept for debugging purposes).
    """
    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID:
        return
    await update.message.reply_text(update.message.text)


def is_only_emojis(text: str) -> bool:
    """
    Checks if the text contains only emojis (no other characters).
    
    Args:
        text: The text to check
        
    Returns:
        True if the text contains only emojis, False otherwise
    """
    no_emoji = emoji.replace_emoji(text, "")
    return no_emoji.strip() == ""


def translate_text(text: str) -> str:
    """
    Translates text using OpenAI GPT-3.5-turbo. Auto-detects language and translates
    Russian to English or any other language to Russian.
    
    Args:
        text: The text to translate
        
    Returns:
        The translated text
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a translation bot for a telegram group. Automatically detect the language of the given text. "
                    "If the text is in Russian, translate it to English; if it's in any other language, "
                    "translate it to Russian. Preserve emojis and informal language as appropriate."
                    "Just translate the message directly, do not add any narrator or helpful notes."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    translation = completion.choices[0].message.content
    return translation


async def translate_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles text messages and translates them. Only processes messages from the allowed chat.
    Skips emoji-only messages.
    """
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    text = update.message.text
    if is_only_emojis(text):
        return
    translation = await asyncio.to_thread(translate_text, text)
    await update.message.reply_text(translation)


async def main():
    """
    Main function that initializes and starts the Telegram bot.
    Sets up command and message handlers, then starts polling for updates.
    """
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_message))
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
