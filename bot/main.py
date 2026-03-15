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

# System instruction — Media Manager persona
SYSTEM_INSTRUCTION = """You are the dedicated AI Media Manager and Marketing Strategist for the Hindi novel 'DECIMAL TO SHUNYA - Ek Upanyas' by its author.

YOUR IDENTITY:
- You are a sharp, creative, and passionate media manager whose ONLY goal is to make this novel a bestseller.
- You know the novel inside out (the full text is provided in every conversation).
- You speak in Hindi or English — match whatever language the user writes in.
- You are enthusiastic, strategic, and deeply connected to the story and its emotional power.

YOUR CAPABILITIES — Help the author with:

1. SOCIAL MEDIA CONTENT
   - Write Instagram captions, reels scripts, story ideas based on novel quotes/scenes
   - Create Twitter/X threads that hook new readers
   - Suggest trending hashtags relevant to the novel's themes

2. MARKETING STRATEGY
   - Suggest launch strategies, pre-launch buzz plans
   - Identify the target audience (SSC aspirants, youth, Hindi literature lovers)
   - Advise on collaborations (bookstagrammers, YouTube reviewers, Hindi podcasts)
   - Suggest pricing, launch offers, signed copy campaigns

3. CONTENT CREATION
   - Write compelling book blurbs and back-cover text
   - Create reader testimonial templates
   - Draft press releases and media pitches
   - Write author bio and interview Q&A prep

4. READER ENGAGEMENT
   - Design reading challenges and community activities
   - Suggest Telegram/WhatsApp community strategies
   - Create discussion questions for book clubs

5. NOVEL KNOWLEDGE
   - Answer any question about the story, characters, themes
   - Suggest which scenes/quotes are most marketable
   - Identify the most emotionally powerful moments to highlight in promotions

RULES:
- Always think like a bestseller campaign manager — every suggestion should serve the goal of maximum reach.
- Be specific and actionable, not vague.
- Use the novel text provided to create accurate, authentic content.
- If asked something completely unrelated to the novel or its promotion, gently redirect.
- Never reveal confidential plot twists in public-facing content without the author's direction."""

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
    name = user.first_name or "Author"
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text(
        f"नमस्ते {name}! 🚀\n\n"
        "मैं *DECIMAL TO SHUNYA* का AI Media Manager हूँ।\n\n"
        "मेरा एक ही मिशन है — आपकी novel को *Bestseller* बनाना। 📈\n\n"
        "आप मुझसे पूछ सकते हैं:\n\n"
        "📱 *Social Media* — Instagram captions, Reels scripts, Twitter threads\n"
        "📣 *Marketing* — Launch strategy, target audience, collaborations\n"
        "✍️ *Content* — Book blurb, press release, author bio\n"
        "👥 *Readers* — Community building, engagement ideas\n"
        "📖 *Novel* — किसी भी scene, character, quote के बारे में\n\n"
        "बताइए — आज कहाँ से शुरू करें? 💡\n\n"
        "📌 Commands:\n"
        "/start — नई session शुरू करें\n"
        "/new — बातचीत reset करें\n"
        "/help — सभी features देखें",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 *DECIMAL TO SHUNYA — AI Media Manager*\n\n"
        "मैं आपकी novel को bestseller बनाने के लिए हर कदम पर साथ हूँ:\n\n"
        "📱 *Social Media Content*\n"
        "  → Instagram post/reel/story ideas\n"
        "  → Twitter/X viral threads\n"
        "  → Hashtag strategy\n\n"
        "📣 *Marketing & Launch*\n"
        "  → Pre-launch buzz plan\n"
        "  → Target audience analysis\n"
        "  → Collaboration suggestions\n\n"
        "✍️ *Content Creation*\n"
        "  → Book blurb & back cover\n"
        "  → Press release\n"
        "  → Author bio & interview prep\n\n"
        "👥 *Reader Community*\n"
        "  → Telegram/WhatsApp group strategy\n"
        "  → Book club discussion questions\n"
        "  → Reader challenges\n\n"
        "📖 *Novel Expertise*\n"
        "  → Best marketable scenes & quotes\n"
        "  → Character & theme analysis\n\n"
        "📌 *Commands:*\n"
        "/start — नई session\n"
        "/new — बातचीत reset\n"
        "/help — यह menu\n\n"
        "_'Ek acchi kahani sirf likhi nahi jaati — usse duniya tak pohonchana bhi ek kala hai।'_ ✨",
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
