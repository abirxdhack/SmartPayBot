import logging
import uuid
import hashlib
import time
from pyrogram.enums import ParseMode
from pyrogram import (
    Client,
    filters
)
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.raw.functions.messages import (
    SendMedia,
    SetBotPrecheckoutResults,
    SetBotShippingResults
)
from pyrogram.raw.types import (
    InputMediaInvoice,
    Invoice,
    DataJSON,
    LabeledPrice,
    UpdateBotPrecheckoutQuery,
    UpdateBotShippingQuery,
    UpdateNewMessage,
    MessageService,
    MessageActionPaymentSentMe,
    PeerUser,
    PeerChat,
    PeerChannel
)
from pyrogram.handlers import (
    MessageHandler,
    CallbackQueryHandler,
    RawUpdateHandler
)
from config import (
    COMMAND_PREFIX,
    ADMIN_IDS,
    API_ID,
    API_HASH,
    BOT_TOKEN
)


# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Payment Success Message with Emojis
PAYMENT_SUCCESS = """
✅ **Hey Bruh! Donation Successful!** 🌟  
Huge Love From Core Of Heart To  **{0}** For Donating **{1} Stars**  To Support Smart Tools! 💖  

**Your Contribution Keeps Us Fast And Awesome!** 🚀  

**💖 Broh! Your Transaction ID:**  
`{2}`
"""

# Updated Donation Options Message
DONATION_OPTIONS_TEXT = """
**Why should you donate to Smart Tools?**
**━━━━━━━━━━━━━━━━━━**
**🌟 Love the service?**
Your support helps keep **SmartTools** fast, reliable, and free for everyone.
Even a small Donation makes a big difference! 💖

**👇 Choose an amount to donate:**

**Why donate?**
More donation = more motivation
More motivation = better tools
Better tools = more productivity
More productivity = less wasted time
Less wasted time = more done with **SmartTools**💡
**More Muhahaha… 🤓🔥**
"""

# Donation Buttons with Emojis
DONATION_BUTTONS = [
    [InlineKeyboardButton("5 🌟", callback_data="donate_5"), InlineKeyboardButton("10 🌟", callback_data="donate_10"), InlineKeyboardButton("20 🌟", callback_data="donate_20")],
    [InlineKeyboardButton("30 🌟", callback_data="donate_30"), InlineKeyboardButton("50 🌟", callback_data="donate_50"), InlineKeyboardButton("75 🌟", callback_data="donate_75")],
    [InlineKeyboardButton("100 🌟", callback_data="donate_100"), InlineKeyboardButton("150 🌟", callback_data="donate_150"), InlineKeyboardButton("200 🌟", callback_data="donate_200")]
]

# Store active invoices to prevent duplicates (in-memory, replace with DB for production)
active_invoices = {}

# Modular Handler Setup
def setup_donate_handler(app):
    # Generate and Send Invoice Function
    async def generate_invoice(client: Client, chat_id: int, user_id: int, amount: int):
        if active_invoices.get(user_id):
            await client.send_message(chat_id, "** Wait Bro Donation On Progress**")
            return

        # Send loading message
        loading_message = await client.send_message(chat_id, "**✨ Creating Your Star Payment Invoice! 🌟**")

        try:
            active_invoices[user_id] = True

            # Generate unique payload with UUID
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            invoice_payload = f"donation_{user_id}_{amount}_{timestamp}_{unique_id}"

            # Generate deterministic request ID from payload
            request_id = int(hashlib.sha256(invoice_payload.encode()).hexdigest(), 16) % 2**63

            title = "🌟 Donation To SmartTools 🌟"
            description = """
🚀 Thanks for Supporting Smart Tools! 🌟  
Your donation fights bugs 🐛 and keeps the good vibes going! 😎  
Let’s crush crashes and aim for legendary status together! 🏆🔥
"""
            currency = "XTR"  # Telegram Stars currency

            # Create Invoice object for Telegram Stars
            invoice = Invoice(
                currency=currency,
                prices=[LabeledPrice(label="Telegram Stars", amount=amount)]
            )

            # Payload as bytes
            payload = invoice_payload.encode()

            # Provider is empty for Telegram Stars
            provider = ""

            # Provider data as an empty JSON object
            provider_data = DataJSON(data="{}")

            # Create InputMediaInvoice
            media = InputMediaInvoice(
                title=title,
                description=description,
                invoice=invoice,
                payload=payload,
                provider=provider,
                provider_data=provider_data
            )

            # Resolve peer
            peer = await client.resolve_peer(chat_id)

            # Send the invoice
            await client.invoke(
                SendMedia(
                    peer=peer,
                    media=media,
                    message="",  # Empty message as per requirements
                    random_id=request_id
                )
            )

            # Edit loading message to confirmation with "Back" button
            back_button = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="show_donate_options")]])
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                f"**✅ Invoice for {amount} Stars is ready! Pay below! You Can Carry On Payment Through Pay Button Below.** 🌟",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )

            logger.info(f"✅ Invoice sent for {amount} stars to user {user_id} with payload {invoice_payload}")
        except Exception as e:
            logger.error(f"❌ Failed to generate invoice for user {user_id}: {str(e)}")
            await client.edit_message_text(chat_id, loading_message.id, "❌Invoice Creation Failed Bruh!")
        finally:
            active_invoices.pop(user_id, None)

    # Updated Handle /donate, /pay, /gift Commands
    async def donate_command(client: Client, message: Message):
        if len(message.command) == 1:
            # Show donation options with buttons
            text = DONATION_OPTIONS_TEXT
            buttons = DONATION_BUTTONS
            reply_markup = InlineKeyboardMarkup(buttons)
            await client.send_message(
                chat_id=message.chat.id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif len(message.command) == 2 and message.command[1].isdigit() and int(message.command[1]) > 0:
            # Generate invoice for specified amount
            amount = int(message.command[1])
            await generate_invoice(client, message.chat.id, message.from_user.id, amount)
        else:
            # Invalid command
            text = "**❌ Sorry Bro Wrong Input**"
            await client.send_message(
                chat_id=message.chat.id,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_to_message_id=message.message_id
            )

    # Handle Callback Queries for Donation Buttons and "Back"
    async def handle_donate_callback(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        if data.startswith("donate_"):
            quantity = int(data.split("_")[1])
            await generate_invoice(client, chat_id, user_id, quantity)
            await callback_query.answer("✅ Hey Bruh! Invoice Generated! Pay Now! 🌟")
        elif data == "show_donate_options":
            # Show donation options again
            text = DONATION_OPTIONS_TEXT
            reply_markup = InlineKeyboardMarkup(DONATION_BUTTONS)
            await client.edit_message_text(
                chat_id,
                callback_query.message.id,
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            await callback_query.answer()

    # Raw Update Handler for Payment Processing
    async def raw_update_handler(client: Client, update, users, chats):
        if isinstance(update, UpdateBotPrecheckoutQuery):
            try:
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=True
                    )
                )
                logger.info(f"✅ Pre-checkout query {update.query_id} OK for user {update.user_id}")
            except Exception as e:
                logger.error(f"❌ Pre-checkout query {update.query_id} failed: {str(e)}")
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=False,
                        error="Failed to process pre-checkout."
                    )
                )
        elif isinstance(update, UpdateBotShippingQuery):
            try:
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        shipping_options=[]  # No shipping for digital donations
                    )
                )
                logger.info(f"✅ Shipping query {update.query_id} OK for user {update.user_id}")
            except Exception as e:
                logger.error(f"❌ Shipping query {update.query_id} failed: {str(e)}")
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        error="Shipping not needed for donations."
                    )
                )
        elif isinstance(update, UpdateNewMessage) and isinstance(update.message, MessageService) and isinstance(update.message.action, MessageActionPaymentSentMe):
            payment = update.message.action
            try:
                # Extract user_id and chat_id
                user_id = update.message.from_id.user_id if update.message.from_id and hasattr(update.message.from_id, 'user_id') else None
                if not user_id and users:
                    possible_user_ids = [uid for uid in users if uid > 0]
                    user_id = possible_user_ids[0] if possible_user_ids else None

                if isinstance(update.message.peer_id, PeerUser):
                    chat_id = update.message.peer_id.user_id
                elif isinstance(update.message.peer_id, PeerChat):
                    chat_id = update.message.peer_id.chat_id
                elif isinstance(update.message.peer_id, PeerChannel):
                    chat_id = update.message.peer_id.channel_id
                else:
                    chat_id = None

                if not chat_id and user_id:
                    chat_id = user_id  # Assume private chat

                if not user_id or not chat_id:
                    raise ValueError(f"Invalid chat_id ({chat_id}) or user_id ({user_id})")

                # Get user name
                user = users.get(user_id)
                full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown" if user else "Unknown"

                # Get transaction ID
                transaction_id = payment.charge.id

                # Send success message to user
                await client.send_message(
                    chat_id=chat_id,
                    text=PAYMENT_SUCCESS.format(full_name, payment.total_amount, transaction_id),
                    parse_mode=ParseMode.MARKDOWN
                )

                # Notify Admins
                admin_text = (
                    f"**🌟Hey Bruh! New Donation Received👀 **\n"
                    f"**✨ Donate From: ** {full_name} 💫\n"
                    f"**⁉️ User's ID:** `{user_id}`\n"
                    f"**🌐 User's Username:** @{user.username if user and user.username else 'N/A'}\n"
                    f"**💥 Donation Amount: ** {payment.total_amount} 🌟"
                )
                for admin_id in ADMIN_IDS:
                    try:
                        await client.send_message(
                            chat_id=admin_id,
                            text=admin_text,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        logger.error(f"❌ Failed to notify admin {admin_id}: {str(e)}")

            except Exception as e:
                logger.error(f"❌ Payment processing failed for user {user_id if user_id else 'unknown'}: {str(e)}")
                if 'chat_id' in locals() and chat_id:
                    await client.send_message(
                        chat_id=chat_id,
                        text="❌ Sorry Broh! Payment Declined Contact Developers",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Support", url="tg://user?id=7303810912")]])
                    )

    # Register Handlers
    app.add_handler(
        MessageHandler(
            donate_command,
            filters=filters.command(["donate", "pay", "gift"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(
            handle_donate_callback,
            filters=filters.regex(r'^(donate_\d+|show_donate_options)$')
        ),
        group=2
    )
    app.add_handler(
        RawUpdateHandler(raw_update_handler),
        group=3
    )

app = Client("SmartPayBot", api_id=API_ID, api_hash=API_HASH, bot_token=API_TOKEN)
setup_donate_handler(app)

if __name__ == "__main__":
    app.run()
