import os
import asyncio
import logging
from itertools import cycle
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
#                   1. CONFIGURATION
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN") 
ADMIN_ID = os.environ.get("ADMIN_ID")  # Your Telegram ID for payment notifications

PAYPAL_EMAILS = [
    os.environ.get("PAYPAL_EMAIL_1", "error_paypal_1@example.com"),
    os.environ.get("PAYPAL_EMAIL_2", "error_paypal_2@example.com")
]
USDT_ADDRESS = os.environ.get("USDT_ADDRESS", "error_usdt_address")

paypal_iterator = cycle(PAYPAL_EMAILS)

USDT_QR_PATH = "usdt_qr.png" 
ALIPAY_QR_PATH = "alipay_qr.png" 
WELCOME_PHOTO_PATH = "welcome_photo.jpg" 

# =========================================================
#                 2. FSM States
# =========================================================

class PaymentStates(StatesGroup):
    waiting_screenshot = State()

# =========================================================
#                 3. Initialization
# =========================================================

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

# =========================================================
#                 4. KEYBOARDS
# =========================================================

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 PAYMENT", callback_data="payment_methods")]
])

payment_methods_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="PayPal", callback_data="pay_paypal")],
    [InlineKeyboardButton(text="USDT (TRC20)", callback_data="pay_usdt")],
    [InlineKeyboardButton(text="AliPay", callback_data="pay_alipay")],
    [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_main")]
])

payment_confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ I Paid", callback_data="confirm_paid")],
    [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_payment_methods")]
])

# =========================================================
#                 5. HANDLERS
# =========================================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    if os.path.exists(WELCOME_PHOTO_PATH):
        welcome_photo = FSInputFile(WELCOME_PHOTO_PATH)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=welcome_photo,
            caption="👋 Welcome!\n\nPlease select a payment method below:",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "👋 Welcome!\n\nPlease select a payment method below:",
            reply_markup=main_menu
        )

@dp.callback_query(F.data == "payment_methods")
async def show_payment_methods(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="💰 Select your payment method:",
        reply_markup=payment_methods_keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    if os.path.exists(WELCOME_PHOTO_PATH):
        welcome_photo = FSInputFile(WELCOME_PHOTO_PATH)
        await callback.message.delete()
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=welcome_photo,
            caption="👋 Welcome!\n\nPlease select a payment method below:",
            reply_markup=main_menu
        )
    else:
        await callback.message.edit_caption(
            caption="👋 Welcome!\n\nPlease select a payment method below:",
            reply_markup=main_menu
        )
    await callback.answer()

@dp.callback_query(F.data == "back_to_payment_methods")
async def back_to_payment_methods(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    # Удаляем текущее сообщение (с QR-кодом если была картинка)
    await callback.message.delete()
    
    # Отправляем новое сообщение с меню выбора способов оплаты
    if os.path.exists(WELCOME_PHOTO_PATH):
        welcome_photo = FSInputFile(WELCOME_PHOTO_PATH)
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=welcome_photo,
            caption="💰 Select your payment method:",
            reply_markup=payment_methods_keyboard
        )
    else:
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text="💰 Select your payment method:",
            reply_markup=payment_methods_keyboard
        )
    
    await callback.answer()

@dp.callback_query(F.data == "pay_paypal")
async def pay_paypal(callback: types.CallbackQuery):
    current_paypal_email = next(paypal_iterator)
    message_text = (
        f"💳 **PayPal**\n\n"
        f"Send payment to:\n"
        f"**{current_paypal_email}**\n\n"
        f"After payment, click **I Paid**."
    )
    await callback.message.edit_caption(
        caption=message_text,
        reply_markup=payment_confirm_keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "pay_usdt")
async def pay_usdt(callback: types.CallbackQuery):
    if os.path.exists(USDT_QR_PATH):
        qr_photo = FSInputFile(USDT_QR_PATH)
        message_text = (
            f"💰 **USDT (TRC20)**\n\n"
            f"Payment address:\n"
            f"`{USDT_ADDRESS}`\n\n"
            f"After payment, click **I Paid**."
        )
        await callback.message.delete()
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=qr_photo,
            caption=message_text,
            reply_markup=payment_confirm_keyboard,
            parse_mode="Markdown"
        )
    else:
        message_text = f"💰 **USDT (TRC20)**\n\nAddress: `{USDT_ADDRESS}`\n\nAfter payment, click **I Paid**."
        await callback.message.edit_caption(
            caption=message_text,
            reply_markup=payment_confirm_keyboard,
            parse_mode="Markdown"
        )
    await callback.answer()

@dp.callback_query(F.data == "pay_alipay")
async def pay_alipay(callback: types.CallbackQuery):
    if os.path.exists(ALIPAY_QR_PATH):
        qr_photo = FSInputFile(ALIPAY_QR_PATH)
        message_text = (
            f"🇨🇳 **AliPay**\n\n"
            f"Scan the QR code to pay.\n\n"
            f"After payment, click **I Paid**."
        )
        await callback.message.delete()
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=qr_photo,
            caption=message_text,
            reply_markup=payment_confirm_keyboard
        )
    else:
        await callback.message.edit_caption(
            caption="🇨🇳 **AliPay**\n\nQR code not found. After payment, click **I Paid**.",
            reply_markup=payment_confirm_keyboard
        )
    await callback.answer()

@dp.callback_query(F.data == "confirm_paid")
async def confirm_paid(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_screenshot)
    await callback.message.answer(
        "📸 Please send a **screenshot** of your payment confirmation."
    )
    await callback.answer()

@dp.message(PaymentStates.waiting_screenshot, F.photo)
async def process_screenshot(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Send notification to admin
    if ADMIN_ID:
        try:
            await bot.send_photo(
                chat_id=int(ADMIN_ID),
                photo=message.photo[-1].file_id,
                caption=f"💰 **New Payment Received!**\n\n"
                        f"👤 From: @{message.from_user.username or 'no username'}\n"
                        f"🆔 User ID: `{message.from_user.id}`\n"
                        f"📝 Name: {message.from_user.full_name}\n\n"
                        f"Please verify the payment screenshot.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send notification to admin: {e}")
    
    # First message - payment confirmation
    await message.answer(
        "✅ **Screenshot received.**\n\n"
        "My working hours are **9:00 AM – 8:00 PM (Indochina Time)**. Please wait for payment confirmation — once it's confirmed, you'll receive the guide right away.",
        parse_mode="Markdown"
    )
    
    # Second message - social media links
    await message.answer(
        "📱 **For more content follow:**\n\n"
        "🎵 TikTok: @follow.kat\n"
        "📸 Instagram: @follow.kat\n"
        "💬 Telegram: katknows russian\n"
        "🔗 LinkTree: https://linktr.ee/katknows",
        parse_mode="Markdown"
    )

@dp.message(PaymentStates.waiting_screenshot)
async def waiting_photo_text(message: types.Message):
    await message.answer("📸 Please send a **screenshot** (photo), not text.")

# =========================================================
#                       6. START
# =========================================================

async def main():
    logger.info("🤖 Starting bot...")
    logger.info(f"Bot username: @katknowsbot")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
