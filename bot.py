import os
import logging
import httpx 
import urllib.parse #just added
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import(
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)

from groq import Groq

# Load API keys from .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY","")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("MODEL","llama-3.3-70b-versatile")

# IN MEMORY HISTORY
#Stores conversation context per telegram user_id

user_histories = {}

#LOGGING
logging.basicConfig(
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level = logging.INFO
)

#Start command: reset chat and welcome user
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clears session history and welcomes user."""
    user_id = update.effective_user.id
    user_histories[user_id] = [] #reset history

    await update.message.reply_text(
         "🤖 *AI Bot Activated!*\n\n"
         "You can now chat with the AI.\n"
         "• Send any message and I will reply.\n"
         "• Use `/image <prompt>` to generate an image.\n\n"
         "Powered by *Groq AI* + *Pollinations*",
         parse_mode="Markdown"  
    )

    #reset command
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = [] 

    await update.message.reply_text(
        "*Chat reset!*\nYour conversation history has been cleared.",
        parse_mode='Markdown'
    )    


#  image command pollination
async def image_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generates an image using Pollinations AI."""

    #Ensure the user provided a prompt
    if not context.args:
        await update.message.reply_text(
            "Please provide a prompt.\nUsage: /image a dog driving a car"
        )
        return   
    
    #Join args into prompts
    prompt = " ".join(context.args)

    #Encode the prompt so it is safe to embed in a url
    try:
        encoded_prompt = urllib.parse.quote(prompt) #just added
    except Exception:
        encoded_prompt = prompt.replace(" ", "%20")

    #pollinations URL
    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}" #just added
        f"?width=512&height=512&model=flux&enhance=true"
    )   

    try:
        #pass url directly to telegram, telegram fetces te images from the uRl
        await update.message.reply_photo(
            photo = image_url,
            caption = f" *Prompt:* {prompt}",
            parse_mode = 'Markdown'
        ) 
    except Exception as e:
        logging.error(f"Image error: {e}")
        await update.message.reply_text(
            "Error fetching image. Try a different prompt"
        )

#Text Message: Groq chat 
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles normal text messages using Groq AI."""
    user_id = update.effective_user.id
    user_text = update.message.text

    #Initialize history for first time users
    if user_id not in user_histories:
        user_histories[user_id] = []

    # save/append uer messages to their history
    user_histories[user_id].append({"role": "user", "content": user_text})  

    #last 10 messages for context
    history = user_histories[user_id][-10:]

    #show typing indicator while waiting for Groq 
    await update.message.chat.send_action("typing")   
    
    #headers and payload for Groq API
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": history,
        "stream": False
    }

    try:
        #Make api calls
        async with httpx.AsyncClient(timeout=40) as client:
            response = await client.post(GROQ_URL, headers=headers, json=payload)

        if response.status_code != 200:
            logging.error(f"Groq API Error: {response.text}")
            await update.message.reply_text(
                "Groq API error. Please try again later"
            ) 
            return
        #assistant reply
        data = response.json() 
        reply = data["choices"][0]["message"]["content"]

        #save assistant reply to maintain conversation context
        user_histories[user_id].append({"role": "assistant", "content": reply}) 

        #reply to user
        await update.message.reply_text(reply)

    except Exception as e:
        logging.error(f"Chat Error: {e}")
        await update.message.reply_text(
            "something went wrong. Please try again"
        )

#Main entry point
if __name__  == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    #Register commands before the general message handler
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("image",image_gen))
    
    #handles plain texts(non command messages)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    print(f"Bot started successfully! Model: {MODEL}")
    app.run_polling()
