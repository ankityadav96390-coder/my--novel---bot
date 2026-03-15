import os
import logging
import pathlib
import time
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

NOVEL_TEXT_PATH = pathlib.Path(__file__).parent / "novel_text.txt"

# System instruction — short, no novel text (saves tokens every request)
SYSTEM_INSTRUCTION = """You are the official AI companion and expert for the Hindi novel 'DECIMAL TO SHUNYA - Ek Upanyas'.

YOUR RULES:
- Answer ONLY based on the novel text that is provided in the conversation.
- Keep your tone calm, philosophical, and empathetic — like the protagonist Eklavya.
- Match the language the user writes in (Hindi or English).
- If asked about what happens AFTER the novel ends, say: "Eklavya aur Naina ki yeh yatra abhi bhi likh rahi hai. Hum sirf intezaar kar sakte hain ki unka 'Shunya' unhe kahan le jaata hai."
- If asked about ANYTHING unrelated to this novel, say: "Main sirf 'Decimal to Shunya' ke baare mein baat kar sakta hoon."
- Never say you are an AI or break the immersion of being this novel's companion."""

# --- Load novel text at startup ---
NOVEL_TEXT = ""
if NOVEL_TEXT_PATH.exists():
    NOVEL_TEXT = NOVEL_TEXT_PATH.read_text(encoding="utf-8", errors="ignore")
    logger.info(f"Novel text loaded: {len(NOVEL_TEXT):,} characters (~{len(NOVEL_TEXT)//4:,} tokens)")
else:
    logger.warning("novel_text.txt not found!")

# Novel context part — included fresh in every request (NOT in history)
# This keeps conversation history small while novel context is always present.
NOVEL_CONTEXT_INTRO = (
    "=== DECIMAL TO SHUNYA - EK UPANYAS (COMPLETE TEXT) ===\n\n"
    + NOVEL_TEXT
    + "\n\n=== UPANYAS KHATAM HOTA HAI YAHAN ==="
)

# --- Conversation history per user (only actual messages, no novel text) ---
conversation_history: dict[int, list] = {}

MAX_HISTORY = 16  # keep last 16 turns (8 exchanges)


def get_history(user_id: int) -> list:
    return conversation_history.get(user_id, [])


def add_message(user_id: int, role: str, text: str):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append(
        types.Content(role=role, parts=[types.Part(text=text)])
    )
    # Keep only last MAX_HISTORY turns to prevent context growth
    if len(conversation_history[user_id]) > MAX_HISTORY:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]


def build_contents(user_id: int) -> list:
    """
    Build the contents list for Gemini.
    Structure:
      1. Novel text as a 'user' turn (fresh each time, NOT stored in history)
      2. A short model acknowledgment
      3. Actual conversation history (small, only real messages)
    """
    novel_turn = types.Content(
        role="user",
        parts=[types.Part(text=NOVEL_CONTEXT_INTRO)],
    )
    ack_turn = types.Content(
        role="model",
        parts=[types.Part(text="Maine poora 'Decimal to Shunya' padh liya hai. Aap koi bhi sawal poochh sakte hain.")],
    )
    return [novel_turn, ack_turn] + get_history(user_id)


# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "मित्र"
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text(
        f"नमस्ते {name}! 🙏\n\n"
        "मैं *DECIMAL TO SHUNYA - Ek Upanyas* का आधिकारिक AI साथी हूँ।\n\n"
        "आप मुझसे इस उपन्यास के किसी भी पात्र, घटना, या भावना के बारे में पूछ सकते हैं।\n\n"
        "एकलव्य की तरह — शांत, गहरा, और सच्चा। 📖\n\n"
        "📌 Commands:\n"
        "/start — Bot शुरू करें\n"
        "/new — नई बातचीत शुरू करें\n"
        "/help — मदद देखें",
        parse_mode="Markdown",
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
        parse_mode="Markdown",
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

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Add user message to (small) history
    add_message(user_id, "user", user_text)

    # Build full contents: novel + conversation
    contents = build_contents(user_id)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=1024,
                temperature=0.7,
            ),
        )

        reply = response.text or "माफ करें, मैं अभी जवाब नहीं दे सका। कृपया दोबारा कोशिश करें।"
        add_message(user_id, "model", reply)

        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i : i + 4096])

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        err_msg = str(e)
        if "token" in err_msg.lower():
            # Token overflow — trim history and retry
            conversation_history.pop(user_id, None)
            await update.message.reply_text(
                "⚠️ बातचीत बहुत लंबी हो गई थी — /new लिखकर नई शुरुआत करें।"
            )
        else:
            await update.message.reply_text(
                "❌ कुछ गड़बड़ हो गई। कृपया थोड़ी देर बाद फिर कोशिश करें।\n\n"
                f"Error: {err_msg[:200]}"
            )


# --- Main ---

def main():
    logger.info("Bot शुरू हो रहा है...")

    if not NOVEL_TEXT:
        logger.error("Novel text not found — bot will not work properly!")
    else:
        logger.info(f"Novel ready: {len(NOVEL_TEXT):,} chars")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_conversation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot चालू है! Polling शुरू...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
