import os
import asyncio
import logging
from itertools import cycle
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
#                   1. КОНФИГУРАЦИЯ
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN") 

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
#                 2. Инициализация
# =========================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================================================
#                 3. КЛАВИАТУРЫ
# =========================================================

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="ОПЛАТА", callback_data="payment_methods")]
])

payment_methods_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="PayPal", callback_data="pay_paypal")],
    [InlineKeyboardButton(text="USDT (TRC20)", callback_data="pay_usdt")],
    [InlineKeyboardButton(text="AliPay", callback_data="pay_alipay")],
    [InlineKeyboardButton(text="🔙 НАЗАД", callback_data="back_to_main")]
])

# =========================================================
#                 4. ХЕНДЛЕРЫ
# =========================================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if os.path.exists(WELCOME_PHOTO_PATH):
        welcome_photo = FSInputFile(WELCOME_PHOTO_PATH)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=welcome_photo,
            caption="Добро пожаловать! Выберите способ оплаты.",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "Добро пожаловать! Выберите способ оплаты.",
            reply_markup=main_menu
        )

@dp.callback_query(F.data == "payment_methods")
async def show_payment_methods(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="Выберите способ оплаты:",
        reply_markup=payment_methods_keyboard
    )
    await callback.answer() 

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: types.CallbackQuery):
    if os.path.exists(WELCOME_PHOTO_PATH):
        welcome_photo = FSInputFile(WELCOME_PHOTO_PATH)
        await callback.message.delete()
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=welcome_photo,
            caption="Добро пожаловать! Выберите способ оплаты.",
            reply_markup=main_menu
        )
    else:
        await callback.message.edit_caption(
            caption="Добро пожаловать! Выберите способ оплаты.",
            reply_markup=main_menu
        )
    await callback.answer()

@dp.callback_query(F.data == "pay_paypal")
async def pay_paypal(callback: types.CallbackQuery):
    current_paypal_email = next(paypal_iterator) 
    message_text = (
        f"💳 **PayPal Оплата**\n\n"
        f"Отправьте оплату на:\n"
        f"**{current_paypal_email}**\n\n"
        f"После оплаты отправьте скриншот в чат."
    )
    await callback.message.edit_caption(
        caption=message_text,
        reply_markup=payment_methods_keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "pay_usdt")
async def pay_usdt(callback: types.CallbackQuery):
    if os.path.exists(USDT_QR_PATH):
        qr_photo = FSInputFile(USDT_QR_PATH)
        message_text = (
            f"💰 **USDT (TRC20) Оплата**\n\n"
            f"Адрес:\n`{USDT_ADDRESS}`\n\n"
            f"Отправьте скриншот оплаты в чат."
        )
        await callback.message.delete()
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=qr_photo,
            caption=message_text,
            reply_markup=payment_methods_keyboard,
            parse_mode="Markdown"
        )
    else:
        await callback.message.edit_caption(
            caption=f"USDT адрес: `{USDT_ADDRESS}`",
            reply_markup=payment_methods_keyboard
        )
    await callback.answer()

@dp.callback_query(F.data == "pay_alipay")
async def pay_alipay(callback: types.CallbackQuery):
    if os.path.exists(ALIPAY_QR_PATH):
        qr_photo = FSInputFile(ALIPAY_QR_PATH)
        message_text = (
            f"🇨🇳 **AliPay Оплата**\n\n"
            f"Отсканируйте QR-код для оплаты.\n\n"
            f"Отправьте скриншот в чат."
        )
        await callback.message.delete()
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=qr_photo,
            caption=message_text,
            reply_markup=payment_methods_keyboard
        )
    else:
        await callback.message.edit_caption(
            caption="AliPay: QR-код не найден.", 
            reply_markup=payment_methods_keyboard
        )
    await callback.answer()

# =========================================================
#                       5. ЗАПУСК
# =========================================================

async def main():
    logger.info("🤖 Starting bot...")
    logger.info(f"Bot username: @katknowsbot")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
