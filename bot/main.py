import os
import logging
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Env Vars ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN:
    raise EnvironmentError("TELEGRAM_TOKEN environment variable is not set!")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY environment variable is not set!")

# --- Gemini Client ---
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"

# In-memory conversation history per user: {user_id: [{"role": ..., "parts": [...]}]}
conversation_history: dict[int, list] = {}

SYSTEM_PROMPT = """आप एक helpful, friendly और intelligent AI assistant हैं।
आप हिंदी और English दोनों में बात कर सकते हैं।
User जिस भाषा में लिखे, उसी भाषा में जवाब दें।
अपने जवाब clear, concise और useful रखें।"""


def get_history(user_id: int) -> list:
    return conversation_history.get(user_id, [])


def add_message(user_id: int, role: str, text: str):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append(
        types.Content(role=role, parts=[types.Part(text=text)])
    )
    # Keep last 20 messages to avoid context overflow
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]


# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "दोस्त"
    await update.message.reply_text(
        f"नमस्ते {name}! 🙏\n\n"
        "मैं आपका **Gemini AI Assistant** हूँ।\n\n"
        "आप मुझसे कुछ भी पूछ सकते हैं — हिंदी या English में!\n\n"
        "📌 Commands:\n"
        "/start — Bot शुरू करें\n"
        "/new — नई बातचीत शुरू करें\n"
        "/help — मदद देखें",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Gemini AI Bot - Help*\n\n"
        "बस मुझे कोई भी सवाल या message भेजें!\n\n"
        "📌 *Commands:*\n"
        "/start — Bot शुरू करें\n"
        "/new — नई बातचीत शुरू करें (history clear)\n"
        "/help — यह help message\n\n"
        "💡 *Tips:*\n"
        "• मैं बातचीत का context याद रखता हूँ\n"
        "• /new से पुरानी history हट जाएगी\n"
        "• हिंदी और English दोनों में बात करें",
        parse_mode="Markdown"
    )


async def new_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history.pop(user_id, None)
    await update.message.reply_text(
        "✅ नई बातचीत शुरू हुई!\n\nपुरानी history हट गई। अब कुछ भी पूछें! 😊"
    )


# --- Message Handler ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Add user message to history
    add_message(user_id, "user", user_text)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=get_history(user_id),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=8192,
                temperature=0.7,
            ),
        )

        reply = response.text or "माफ करें, मैं अभी जवाब नहीं दे सका। कृपया दोबारा कोशिश करें।"

        # Add assistant reply to history
        add_message(user_id, "model", reply)

        # Telegram message limit is 4096 chars — split if needed
        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i:i+4096])

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        await update.message.reply_text(
            "❌ कुछ गड़बड़ हो गई। कृपया थोड़ी देर बाद फिर कोशिश करें।\n\n"
            f"Error: {str(e)[:200]}"
        )


# --- Main ---

def main():
    logger.info("Bot शुरू हो रहा है...")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_conversation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot चालू है! Polling शुरू...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
