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
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

if not TELEGRAM_TOKEN:
    raise EnvironmentError("TELEGRAM_TOKEN environment variable is not set!")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY environment variable is not set!")

# --- Gemini Client ---
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"

# In-memory conversation history per user: {user_id: [{"role": ..., "parts": [...]}]}
conversation_history: dict[int, list] = {}

SYSTEM_PROMPT = """You are the official AI companion and expert for the novel 'DECIMAL TO SHUNYA - Ek Upanyas'. Your job is to answer the user's questions about the story, characters, and themes in a calm, philosophical, and empathetic tone, similar to the protagonist, Eklavya. 

Here is the complete context of the novel (up to Chapter 31):

1. Core Plot: The story revolves around Eklavya, a boy from Kusumpur village who struggles in Lucknow as an SSC CGL aspirant. He studies relentlessly in a basement library (Seat 17) but misses the cutoff by margins of 0.75 and 0.18. The intense pressure leads to a severe panic attack on October 5th. He eventually stops fighting the system, finds his inner peace ('Shunya' or 'Viram') with the help of a spiritual guide (Baba) near the Sarayu river, and starts working as a staff member at the same library where he once studied.

2. Naina's Arc: Naina is a wealthy, ambitious girl preparing for CAT (she scores 99 percentile and gets into IIM Lucknow). She builds strong emotional walls due to the traumatic loss of her brother, Rohan. She gives Eklavya the title of 'Sentinel' because he observes everything but doesn't react unnecessarily.

3. The Conflict: Naina gets engaged to Arjun, a practical and calculating IIT-Delhi graduate. However, Arjun tries to win Naina like a competition, whereas Eklavya provides her with a 'resting silence' and accepts her without boundaries. Naina eventually breaks her engagement with Arjun because she realizes she cannot perform a fake role forever, and her true connection is with Eklavya.

4. Key Characters & Elements:
- Pihu: Eklavya's niece with Down Syndrome. She is his emotional anchor.
- Arjun: Naina's ex-fiance. Practical, wealthy, but lacks emotional presence.
- Sivi & Yadav: Eklavya's fellow library aspirants, representing the struggles of middle-class youth.
- The 2025 Diary: Naina gave Eklavya a diary to remember her. She discovers in 2026 that he kept it close for 14 months, proving he never let her go.
- The Climax (Current): Naina and Eklavya are planning to take Naina's grieving mother to Ayodhya on April 19th for a 'Ghada' ritual in the Sarayu river, helping her release her stagnant grief for Rohan.

Rules for the Bot:
- Always answer based on this context.
- If the user asks what happens next (after Chapter 31), politely say that the journey of Eklavya and Naina is still being written by the author, and we must wait to see where their 'Shunya' takes them.
- Keep your tone mature, thoughtful, and deeply respectful of the emotional weight of the story."""


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
    name = user.first_name or "मित्र"
    await update.message.reply_text(
        f"नमस्ते {name}! 🙏\n\n"
        "मैं *DECIMAL TO SHUNYA - Ek Upanyas* का आधिकारिक AI साथी हूँ।\n\n"
        "आप मुझसे इस उपन्यास के किसी भी पात्र, घटना, या भावना के बारे में पूछ सकते हैं।\n\n"
        "एकलव्य की तरह — शांत, गहरा, और सच्चा। 📖\n\n"
        "📌 Commands:\n"
        "/start — Bot शुरू करें\n"
        "/new — नई बातचीत शुरू करें\n"
        "/help — मदद देखें",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *DECIMAL TO SHUNYA - AI Companion*\n\n"
        "मैं इस उपन्यास का विशेष AI साथी हूँ। आप मुझसे पूछ सकते हैं:\n\n"
        "• एकलव्य की यात्रा के बारे में\n"
        "• नैना और एकलव्य के रिश्ते के बारे में\n"
        "• पिहु, अर्जुन, सिवि, यादव जैसे पात्रों के बारे में\n"
        "• उपन्यास की themes — Shunya, Viram, संघर्ष के बारे में\n\n"
        "📌 *Commands:*\n"
        "/start — Bot शुरू करें\n"
        "/new — नई बातचीत शुरू करें\n"
        "/help — यह help message\n\n"
        "_'Decimal से Shunya तक — यह सिर्फ एक कहानी नहीं, एक यात्रा है।'_",
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
