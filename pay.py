import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.messages import SendMedia
from pyrogram.raw.types import InputMediaInvoice, Invoice, DataJSON, LabeledPrice
from pyrogram.enums import ParseMode
import time
from config import COMMAND_PREFIX, API_ID, API_HASH, BOT_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Bot Client From BOT_TOKEN
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Handle the /donate command
@app.on_message(filters.command(["donate", "pay"], prefixes=COMMAND_PREFIX) & filters.private)
def donate_command(client: Client, message: Message):
    text = """
💥 Life throws bugs... I hurl **STARS** and pray for victory! 🚀  
**Support the epic quest to debug **Smart Tools**—and maybe my soul too! 😎💀**  
Choose your **Patch Level** to join the legend:  
- 🌟 More Stars = **More Try/Catch Magic** 🪄  
- 🪄 More Try/Catch = **Fewer Sneaky Crashes** 🐛  
- 🐛 Fewer Crashes = **Epic Uptime Boost** ⚡  
- ⚡ Epic Uptime = **Ultimate Flex Vibes** 💪  
- 💪 Ultimate Flex = **LEGENDARY STATUS UNLOCKED** 🏆  
Become a Legend... Unleash the **MUHAHAHA**! 😈🔥
    """
    buttons = [
        [InlineKeyboardButton("5 🌟", callback_data="donate_5"), InlineKeyboardButton("10 🌟", callback_data="donate_10"), InlineKeyboardButton("20 🌟", callback_data="donate_20")],
        [InlineKeyboardButton("30 🌟", callback_data="donate_30"), InlineKeyboardButton("50 🌟", callback_data="donate_50"), InlineKeyboardButton("75 🌟", callback_data="donate_75")],
        [InlineKeyboardButton("100 🌟", callback_data="donate_100"), InlineKeyboardButton("150 🌟", callback_data="donate_150"), InlineKeyboardButton("200 🌟", callback_data="donate_200")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

# Handle donate callback queries
@app.on_callback_query(filters.regex(r'^donate_\d+$'))
def handle_donate_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    quantity = int(data.split("_")[1])  # Number of stars
    user_id = callback_query.from_user.id
    timestamp = int(time.time())
    invoice_payload = f"donation_{user_id}_{quantity}_{timestamp}"
    chat_id = callback_query.message.chat.id
    title = "🌟 Donation to Smart Tools 🌟"
    description = """
        🚀 Thank You for Powering Smart Tools! 🌟 
        Your generous donation fuels the fight against bugs 🐛 and keeps the epic vibes flowing! 😎  
        Together, we’ll conquer crashes and flex legendary status! 🏆🔥
        """
    currency = "XTR"  # Telegram Stars currency

    # Send temporary loading message
    loading_message = client.send_message(chat_id, "**✨ Creating Star Payment Invoice Button🌟** ")

    try:
        # Create Invoice object for Telegram Stars
        invoice = Invoice(
            currency=currency,
            prices=[LabeledPrice(label="Telegram Stars", amount=quantity)]
        )

        # Payload as bytes
        payload = invoice_payload.encode()

        # Provider is empty for Telegram Stars
        provider = ""

        # Provider data as an empty JSON object
        provider_data = DataJSON(data="{}")

        # Start parameter for Stars
        start_param = "star"

        # Create InputMediaInvoice
        media = InputMediaInvoice(
            title=title,
            description=description,
            invoice=invoice,
            payload=payload,
            provider=provider,
            provider_data=provider_data,
            start_param=start_param
        )

        # Resolve peer (synchronous in Pyrogram)
        peer = client.resolve_peer(chat_id)

        # Send the invoice using raw API
        client.invoke(
            SendMedia(
                peer=peer,
                media=media,
                message="",  # Empty message as per snippet
                random_id=client.rnd_id()
            )
        )

        logger.info(f"Successfully sent invoice for {quantity} stars to user {user_id}")
        callback_query.answer("Invoice Generated Kindly Pay Now🌟")
    except Exception as e:
        logger.error(f"Failed to send invoice: {str(e)}")
        callback_query.answer("Invoice Create API Dead")
    finally:
        # Delete the loading message
        client.delete_messages(chat_id, loading_message.id)

# Start the bot
app.run()