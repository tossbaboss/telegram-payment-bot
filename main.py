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

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
#                   1. КОНФИГУРАЦИЯ
# =========================================================

TOKEN = os.environ.get("BOT_TOKEN") 
ADMIN_ID = os.environ.get("ADMIN_ID")  # Опционально - ID админа для пересылки скринов

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
#                 2. FSM States (для ожидания скриншота)
# =========================================================

class PaymentStates(StatesGroup):
    waiting_screenshot = State()

# =========================================================
#                 3. Инициализация
# =========================================================

storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

# =========================================================
#                 4. КЛАВИАТУРЫ
# =========================================================

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💳 ОПЛАТА", callback_data="payment_methods")]
])

payment_methods_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="PayPal", callback_data="pay_paypal")],
    [InlineKeyboardButton(text="USDT (TRC20)", callback_data="pay_usdt")],
    [InlineKeyboardButton(text="AliPay", callback_data="pay_alipay")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
])

# Клавиатура после выбора способа оплаты
payment_confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ I Paid", callback_data="confirm_paid")],
    [InlineKeyboardButton(text="🔙 Back", callback_data="back_to_payment_methods")]
])

# =========================================================
#                 5. ХЕНДЛЕРЫ
# =========================================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()  # Сбрасываем любое состояние
    
    if os.path.exists(WELCOME_PHOTO_PATH):
        welcome_photo = FSInputFile(WELCOME_PHOTO_PATH)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=welcome_photo,
            caption="👋 Добро пожаловать!\n\nВыберите способ оплаты ниже:",
            reply_markup=main_menu
        )
    else:
        await message.answer(
            "👋 Добро пожаловать!\n\nВыберите способ оплаты ниже:",
            reply_markup=main_menu
        )

@dp.callback_query(F.data == "payment_methods")
async def show_payment_methods(callback: types.CallbackQuery):
    await callback.message.edit_caption(
        caption="💰 Выберите способ оплаты:",
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
            caption="👋 Добро пожаловать!\n\nВыберите способ оплаты ниже:",
            reply_markup=main_menu
        )
    else:
        await callback.message.edit_caption(
            caption="👋 Добро пожаловать!\n\nВыберите способ оплаты ниже:",
            reply_markup=main_menu
        )
    await callback.answer()

@dp.callback_query(F.data == "back_to_payment_methods")
async def back_to_payment_methods(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_caption(
        caption="💰 Выберите способ оплаты:",
        reply_markup=payment_methods_keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "pay_paypal")
async def pay_paypal(callback: types.CallbackQuery):
    current_paypal_email = next(paypal_iterator)
    message_text = (
        f"💳 **PayPal**\n\n"
        f"Отправьте оплату на:\n"
        f"**{current_paypal_email}**\n\n"
        f"После оплаты нажмите **I Paid**."
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
            f"Адрес для оплаты:\n"
            f"`{USDT_ADDRESS}`\n\n"
            f"После оплаты нажмите **I Paid**."
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
        message_text = f"💰 **USDT (TRC20)**\n\nАдрес: `{USDT_ADDRESS}`\n\nПосле оплаты нажмите **I Paid**."
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
            f"Отсканируйте QR-код для оплаты.\n\n"
            f"После оплаты нажмите **I Paid**."
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
            caption="🇨🇳 **AliPay**\n\nQR-код не найден. После оплаты нажмите **I Paid**.",
            reply_markup=payment_confirm_keyboard
        )
    await callback.answer()

# Кнопка "I Paid" - запрашиваем скриншот
@dp.callback_query(F.data == "confirm_paid")
async def confirm_paid(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_screenshot)
    await callback.message.answer(
        "📸 Пожалуйста, отправьте **скриншот** подтверждения оплаты."
    )
    await callback.answer()

# Обработка скриншота
@dp.message(PaymentStates.waiting_screenshot, F.photo)
async def process_screenshot(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Если указан ADMIN_ID - пересылаем скрин админу
    if ADMIN_ID:
        try:
            await bot.send_photo(
                chat_id=int(ADMIN_ID),
                photo=message.photo[-1].file_id,
                caption=f"💰 **Новая оплата!**\n\n"
                        f"От: @{message.from_user.username or 'без username'}\n"
                        f"ID: `{message.from_user.id}`\n"
                        f"Имя: {message.from_user.full_name}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить админу: {e}")
    
    await message.answer(
        "✅ **Скриншот получен!**\n\n"
        "Ваша оплата на проверке. Ожидайте подтверждения.\n\n"
        "Напишите /start чтобы вернуться в главное меню."
    )

# Если прислали текст вместо фото
@dp.message(PaymentStates.waiting_screenshot)
async def waiting_photo_text(message: types.Message):
    await message.answer("📸 Please, send a **screenhot** of your payment (photo).")

# =========================================================
#                       6. ЗАПУСК
# =========================================================

async def main():
    logger.info("🤖 Starting bot...")
    logger.info(f"Bot username: @katknowsbot")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
