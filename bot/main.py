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

NOVEL_FILE_PATH = pathlib.Path(__file__).parent / "novel.txt"

# Short system instruction — NO novel text here (saves tokens every request)
SYSTEM_INSTRUCTION = """You are the official AI companion and expert for the novel 'DECIMAL TO SHUNYA - Ek Upanyas'.

YOUR RULES:
- Answer ONLY based on the novel that has been shared with you at the start of the conversation.
- Keep your tone calm, philosophical, and empathetic — like the protagonist Eklavya.
- Match the language of the user (Hindi or English).
- If asked what happens after the last chapter written, say: "Eklavya aur Naina ki yeh yatra abhi lekh rahi hai. Hum sirf intezaar kar sakte hain ki unka 'Shunya' unhe kahan le jaata hai."
- If asked about ANYTHING unrelated to this novel, gently say: "Main sirf 'Decimal to Shunya' ke baare mein baat kar sakta hoon."
- Never break immersion by saying you are an AI or a bot."""

# --- File API: Upload novel once, reuse URI ---
uploaded_novel: genai.types.File | None = None
novel_upload_time: float = 0
FILE_EXPIRY_SECONDS = 47 * 3600  # Gemini files expire after 48h; re-upload at 47h


def upload_novel() -> genai.types.File | None:
    global uploaded_novel, novel_upload_time
    if not NOVEL_FILE_PATH.exists():
        logger.error("novel.txt not found!")
        return None
    try:
        logger.info("Novel को Gemini File API पर upload कर रहे हैं...")
        file_obj = client.files.upload(
            file=str(NOVEL_FILE_PATH),
            config={"mime_type": "text/plain", "display_name": "Decimal To Shunya - Ek Upanyas"},
        )
        # Wait until file is ACTIVE
        for _ in range(30):
            file_obj = client.files.get(name=file_obj.name)
            if file_obj.state.name == "ACTIVE":
                break
            logger.info("File processing... wait kar rahe hain")
            time.sleep(3)

        uploaded_novel = file_obj
        novel_upload_time = time.time()
        logger.info(f"Novel upload successful! URI: {file_obj.uri}")
        return file_obj
    except Exception as e:
        logger.error(f"Novel upload failed: {e}")
        return None


def get_novel_file() -> genai.types.File | None:
    """Return cached file, re-uploading if expired."""
    global uploaded_novel, novel_upload_time
    if uploaded_novel is None or (time.time() - novel_upload_time) > FILE_EXPIRY_SECONDS:
        return upload_novel()
    return uploaded_novel


# --- Conversation history per user ---
# Each history starts with a seeded "file context" turn so the file is only
# referenced once per conversation, not on every single request.
conversation_history: dict[int, list] = {}


def seed_history(user_id: int):
    """Seed a new conversation with the novel file as context (only once per chat)."""
    novel_file = get_novel_file()
    if novel_file:
        conversation_history[user_id] = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        file_data=types.FileData(
                            file_uri=novel_file.uri,
                            mime_type="text/plain",
                        )
                    ),
                    types.Part(
                        text=(
                            "Yeh 'DECIMAL TO SHUNYA - Ek Upanyas' ka poora text hai. "
                            "Ise dhyan se padho aur apni puri conversation mein isi ke "
                            "aadhar par jawab do."
                        )
                    ),
                ],
            ),
            types.Content(
                role="model",
                parts=[
                    types.Part(
                        text=(
                            "Maine poora upanyas padh liya hai. Aap Eklavya, Naina, Pihu, "
                            "Arjun, Baba, Sivi, Yadav — kisi bhi paatra ya ghatna ke baare "
                            "mein pooch sakte hain. Main aapka intezaar kar raha tha. 🙏"
                        )
                    )
                ],
            ),
        ]
    else:
        # Fallback if upload failed
        conversation_history[user_id] = []


def get_history(user_id: int) -> list:
    if user_id not in conversation_history:
        seed_history(user_id)
    return conversation_history[user_id]


def add_message(user_id: int, role: str, text: str):
    history = get_history(user_id)
    history.append(types.Content(role=role, parts=[types.Part(text=text)]))
    # Keep seed (first 2 items) + last 18 messages to cap context
    if len(history) > 20:
        conversation_history[user_id] = history[:2] + history[-18:]


# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name or "मित्र"
    # Pre-seed conversation so first message is fast
    seed_history(update.effective_user.id)
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

    add_message(user_id, "user", user_text)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=get_history(user_id),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=1024,  # Concise answers save output tokens too
                temperature=0.7,
            ),
        )

        reply = response.text or "माफ करें, मैं अभी जवाब नहीं दे सका। कृपया दोबारा कोशिश करें।"
        add_message(user_id, "model", reply)

        # Telegram message limit is 4096 chars
        if len(reply) <= 4096:
            await update.message.reply_text(reply)
        else:
            for i in range(0, len(reply), 4096):
                await update.message.reply_text(reply[i : i + 4096])

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        # If file expired, reset history so it re-uploads on next message
        if "file" in str(e).lower() or "invalid" in str(e).lower():
            global uploaded_novel
            uploaded_novel = None
            conversation_history.pop(user_id, None)
            await update.message.reply_text(
                "⚠️ Novel context refresh हो रही है। कृपया दोबारा लिखें।"
            )
        else:
            await update.message.reply_text(
                "❌ कुछ गड़बड़ हो गई। कृपया थोड़ी देर बाद फिर कोशिश करें।\n\n"
                f"Error: {str(e)[:200]}"
            )


# --- Main ---

def main():
    logger.info("Bot शुरू हो रहा है...")

    # Upload novel at startup
    upload_novel()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_conversation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot चालू है! Polling शुरू...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
