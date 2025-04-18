import logging
import uuid
import hashlib
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.messages import SendMedia, SetBotPrecheckoutResults, SetBotShippingResults
from pyrogram.raw.types import InputMediaInvoice, Invoice, DataJSON, LabeledPrice, UpdateBotPrecheckoutQuery, UpdateBotShippingQuery, UpdateNewMessage, MessageService, MessageActionPaymentSentMe, PeerUser, PeerChat, PeerChannel
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, RawUpdateHandler
from pyrogram.enums import ParseMode
import time
from config import COMMAND_PREFIX, ADMIN_IDS, API_ID, API_HASH, BOT_TOKEN

# Logger Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Payment Success Message
PAYMENT_SUCCESS = "<b>🎉 Thank you for your donation of {0} ⭐️!</b>\nYour support keeps Smart Tools Alive! 🚀"

# Store active invoice requests to prevent duplicates (in-memory, replace with DB for production)
active_invoices = {}

# Modular handler setup
def setup_donate_handler(app):
    # Handle the /donate and /pay commands in private chats
    async def donate_command(client: Client, message: Message):
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
        await message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    async def handle_donate_callback(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        quantity = int(data.split("_")[1])  # Number of stars
        user_id = callback_query.from_user.id
        chat_id = callback_query.message.chat.id

        # Check for active invoice to prevent duplicates
        if active_invoices.get(user_id):
            await callback_query.answer("Sir Please Wait Donation On Progress")
            return

        # Generate unique payload with UUID
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]  # Short UUID for uniqueness
        invoice_payload = f"donation_{user_id}_{quantity}_{timestamp}_{unique_id}"

        # Generate deterministic request ID from payload
        request_id = int(hashlib.sha256(invoice_payload.encode()).hexdigest(), 16) % 2**63

        title = "🌟 Donation To SmartTools🌟"
        description = """
        🚀 Thank You for Powering Smart Tools! 🌟 
        Your generous donation fuels the fight against bugs 🐛 and keeps the epic vibes flowing! 😎  
        Together, we’ll conquer crashes and flex legendary status! 🏆🔥
        """
        currency = "XTR"  # Telegram Stars currency

        # Send temporary loading message
        loading_message = await client.send_message(chat_id, "**✨ Creating Star Payment Invoice Button🌟** ")

        try:
            # Mark invoice as active
            active_invoices[user_id] = True

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

            # Create InputMediaInvoice (omit start_param)
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

            # Send the invoice using raw API with deterministic request ID
            await client.invoke(
                SendMedia(
                    peer=peer,
                    media=media,
                    message="",  # Empty message as per snippet
                    random_id=request_id  # Deterministic ID based on payload
                )
            )

            logger.info(f"Successfully sent invoice for {quantity} stars to user {user_id} with payload {invoice_payload}, request_id {request_id}")
            await callback_query.answer("Invoice Generated! Kindly Pay Now 🌟")
        except Exception as e:
            logger.error(f"Failed to send invoice for user {user_id}: {str(e)}")
            await callback_query.answer(f"Invoice Create API Dead")
        finally:
            # Delete the loading message
            await client.delete_messages(chat_id, loading_message.id)
            # Remove active invoice lock
            active_invoices.pop(user_id, None)

    async def raw_update_handler(client: Client, update, users, chats):
        if isinstance(update, UpdateBotPrecheckoutQuery):
            try:
                # Acknowledge the pre-checkout query using raw API
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=True
                    )
                )
                logger.info(f"Pre-checkout query {update.query_id} acknowledged for user {update.user_id}")
            except Exception as e:
                logger.error(f"Failed to handle pre-checkout query {update.query_id}: {str(e)}")
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=False,
                        error="Failed to process pre-checkout query."
                    )
                )
        elif isinstance(update, UpdateBotShippingQuery):
            try:
                # Acknowledge the shipping query with empty options (digital goods)
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        shipping_options=[]  # No shipping for digital donations
                    )
                )
                logger.info(f"Shipping query {update.query_id} acknowledged for user {update.user_id}")
            except Exception as e:
                logger.error(f"Failed to handle shipping query {update.query_id}: {str(e)}")
                await client.invoke(
                    SetBotShippingResults(
                        query_id=update.query_id,
                        error="Shipping not required for donations."
                    )
                )
        elif isinstance(update, UpdateNewMessage) and isinstance(update.message, MessageService) and isinstance(update.message.action, MessageActionPaymentSentMe):
            payment = update.message.action
            logger.debug(f"Payment message: {update.message}, from_id: {update.message.from_id}, peer_id: {update.message.peer_id}, users: {users}")

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

                logger.info(f"Payment successful: {payment.payload} for {payment.total_amount} {payment.currency}")

                # Notify User For Payment Success
                await client.send_message(
                    chat_id=chat_id,
                    text=PAYMENT_SUCCESS.format(payment.total_amount),
                    parse_mode=ParseMode.HTML
                )

                # Notify Admins For Donation
                try:
                    user = users.get(user_id, None)
                    full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown" if user else "Unknown"
                    username = f"@{user.username or 'N/A'}" if user else "@N/A"
                    admin_text = (
                        f"<b>🎉 New Donation Rechieved 🎉</b>\n"
                        f"<b>From:</b> {full_name}\n"
                        f"<b>User ID:</b> <code>{user_id}</code>\n"
                        f"<b>Username:</b> {username}\n"
                        f"<b>Amount:</b> {payment.total_amount} ⭐️"
                    )
                    for admin_id in ADMIN_IDS:
                        try:
                            await client.send_message(
                                chat_id=admin_id,
                                text=admin_text,
                                parse_mode=ParseMode.HTML
                            )
                        except Exception as e:
                            logger.error(f"Failed to send admin notification to {admin_id}: {str(e)}")
                except Exception as e:
                    logger.error(f"Failed to send admin notifications for user {user_id}: {str(e)}")

            except Exception as e:
                logger.error(f"Failed to handle successful payment for user {user_id if user_id else 'unknown'}: {str(e)}")
                # Only send error message if user notification failed
                if 'chat_id' in locals() and chat_id and not locals().get('user_notified', False):
                    await client.send_message(
                        chat_id=chat_id,
                        text="Sorry Bro Payment Declined Contact Support",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", url="tg://user?id=7303810912")]])
                    )

    # Register All Handlers For RAW API
    app.add_handler(
        MessageHandler(
            donate_command,
            filters=filters.command(["donate", "pay"], prefixes=COMMAND_PREFIX) & filters.private
        ),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(
            handle_donate_callback,
            filters=filters.regex(r'^donate_\d+$')
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
