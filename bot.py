import logging
import httpx
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "yoou token"
GROQ_API_KEY = "your token"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

# In-memory history (resets on service restart)
user_histories = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets history and greets the user."""
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text(
        "⚡ *AI Assistant Active*\n\n"
        "• Send me a message to chat (Powered by Groq)\n"
        "• Use `/image [prompt]` to generate art (Powered by Pollinations)",
        parse_mode='Markdown'
    )

async def image_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (keep prompt logic) ...
    
    image_url = f"https://pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
    
    try:
        # Instead of 'await client.get(image_url)', just send the URL
        await update.message.reply_photo(
            photo=image_url, 
            caption=f"🎨 *Prompt:* {prompt}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Image Error: {e}")
        await update.message.reply_text("⚠️ Telegram had trouble fetching that image.")
    
    # Encode prompt for URL
    encoded_prompt = httpx.utils.quote(prompt)
    image_url = f"https://pollinations.ai{encoded_prompt}?width=1024&height=1024&seed=42&nologo=true"
    
    try:
        # Increased timeout to 60s to handle slow generation
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            if response.status_code == 200:
                await update.message.reply_photo(
                    photo=response.content, 
                    caption=f"🎨 *Prompt:* {prompt}",
                    parse_mode='Markdown'
                )
            else:
                logging.error(f"Pollinations Status Code: {response.status_code}")
                await update.message.reply_text("⚠️ Image server is currently busy. Please try again.")
    except Exception as e:
        logging.error(f"Image Error: {e}")
        await update.message.reply_text("⌛ Image generation timed out or failed. Please try a simpler prompt.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text chat with Groq."""
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_histories:
        user_histories[user_id] = []

    # Add user message to history
    user_histories[user_id].append({"role": "user", "content": user_text})
    
    # Keep context to last 10 messages
    history = user_histories[user_id][-10:]

    await update.message.chat.send_action("typing")

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL,
            "messages": history,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=40.0) as client:
            response = await client.post(GROQ_URL, headers=headers, json=payload)
            
            if response.status_code != 200:
                logging.error(f"Groq API Error: {response.text}")
                await update.message.reply_text("⚠️ Groq API is currently unavailable.")
                return

            data = response.json()
            reply = data['choices'][0]['message']['content']

            # Save reply to history
            user_histories[user_id].append({"role": "assistant", "content": reply})
            await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Chat Error: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Please try again later.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Register Commands - IMPORTANT: commands must be registered before the general MessageHandler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("image", image_gen))
    
    # Register Message Handler (All text that isn't a command)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Service started. Using model: {MODEL}")
    app.run_polling()
