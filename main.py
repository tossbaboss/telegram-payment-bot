import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, ReplyKeyboardRemove

# =========================================================
#                   1. CONFIGURATION (MANDATORY CHANGES)
# =========================================================

# 1. Your bot token
TOKEN = "8405037254:AAH-YlQCvru2bOXjJe8y3HmQTNF1_StOJRY"  # <--- ЗАМЕНИТЕ ВАШИМ ТОКЕНОМ

# 2. Your Telegram ID (where screenshots will be forwarded)
ADMIN_ID = 1866001822  # <--- ЗАМЕНИТЕ ЭТО ЧИСЛО НА ВАШ ID

# 3. Payment details (ОБНОВЛЕНО: Новый текст для PayPal)
USDT_DETAILS = "USDT (TRC-20) Wallet Address: **TzXXXXXXXXXXXX**\n\nPlease pay the exact amount."

# ИЗМЕНЕНИЕ 1: Обновленный текст с жирным шрифтом
PAYPAL_DETAILS = "Our PayPal: **email@example.com**\n\n" \
                 "**⚠️ IMPORTANT:**\n" \
                 "Please use the **\"Friends and Family\"** option to ensure the full payment is received. " \
                 "If using **\"Goods and Services,\"** **YOU MUST COVER ALL PROCESSING FEES.**"

ALIPAY_DETAILS = "Our Alipay Number: **1234567890**"

# 4. Paths to QR code images
USDT_QR_PATH = "usdt_qr.png" 
ALIPAY_QR_PATH = "alipay_qr.png" 

# 5. Welcome photo path (ПРОВЕРЬТЕ ИМЯ!)
WELCOME_PHOTO_PATH = "welcome_photo.jpg" 

# =========================================================
#                    2. FSM AND INITIALIZATION
# =========================================================

# State machine for screenshot waiting
class PaymentStates(StatesGroup):
    waiting_for_screenshot = State()

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# =========================================================
#                       3. KEYBOARDS
# =========================================================

# Main payment selection keyboard
def get_payment_keyboard():
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="💰 USDt (TRC-20)", callback_data="pay_usdt"),
                types.InlineKeyboardButton(text="💳 PayPal", callback_data="pay_paypal"),
            ],
            [
                types.InlineKeyboardButton(text="💸 Alipay", callback_data="pay_alipay"),
            ]
        ]
    )
    return keyboard

# Confirmation and Back buttons
confirm_and_back_keyboard = types.InlineKeyboardMarkup(
    inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ I Paid", callback_data="confirm_payment"),
            types.InlineKeyboardButton(text="⬅️ Back", callback_data="back_to_menu")
        ]
    ]
)

# =========================================================
#                       4. HANDLERS
# =========================================================

# 1. /start handler 
@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    
    # 1. Remove any stuck ReplyKeyboardMarkup
    await message.answer(
        "Starting bot...",
        reply_markup=ReplyKeyboardRemove() 
    )

    # 2. Send welcome photo and main menu
    try:
        photo_file = FSInputFile(WELCOME_PHOTO_PATH)
        await bot.send_photo(
            chat_id=message.chat.id,
            photo=photo_file,
            caption=f"Hello, {message.from_user.full_name}! 👋\n\n"
                    "Please select your preferred payment method:",
            reply_markup=get_payment_keyboard()
        )
    except FileNotFoundError:
        # Fallback if photo is not found
        await message.answer(
            f"Hello, {message.from_user.full_name}! 👋\n\n"
            "Please select your preferred payment method:",
            reply_markup=get_payment_keyboard()
        )
    except Exception as e:
        # Fallback for other photo errors
        print(f"Error sending photo: {e}")
        await message.answer(
            f"Hello, {message.from_user.full_name}! 👋\n\n"
            "Please select your preferred payment method:",
            reply_markup=get_payment_keyboard()
        )


# 2. Back button handler (ИЗМЕНЕНИЕ 2: Удаляем предыдущее сообщение с реквизитами и перезапускаем меню)
@dp.callback_query(lambda c: c.data == 'back_to_menu')
async def back_to_menu_handler(callback_query: types.CallbackQuery, state: FSMContext):
    
    # 1. Удаляем сообщение с реквизитами (которое содержит кнопку "Назад")
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    
    # 2. Пытаемся удалить предыдущее сообщение (которое было "You have selected...")
    try:
        # УДАЛИТЬ ЛИШНЕЕ СООБЩЕНИЕ ИЗ ЧАТА
        await bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id - 1
        )
    except Exception:
        # Игнорируем ошибку, если сообщение не удалось найти/удалить (например, если оно было старым)
        pass

    # 3. Повторно запускаем /start для возврата к главному меню (с фото)
    await command_start_handler(callback_query.message)
        
    await callback_query.answer()


# 3. Payment selection handler
@dp.callback_query(lambda c: c.data and c.data.startswith('pay_'))
async def process_payment_selection(callback_query: types.CallbackQuery):
    
    method = callback_query.data.split('_')[1]
    details = ""
    send_photo = False
    qr_path = None 

    # 1. РЕДАКТИРУЕМ ПРЕДЫДУЩЕЕ СООБЩЕНИЕ МЕНЮ
    # Изменяем подпись (caption) сообщения с фото.
    try:
        await bot.edit_message_caption(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            caption="You have selected a payment method. Here are the details:",
            reply_markup=None # Убираем кнопки с выбора
        )
    except Exception:
        # Если не удалось отредактировать подпись (например, если было только текст)
        await bot.edit_message_text(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            text="You have selected a payment method. Here are the details:",
            reply_markup=None
        )


    # 2. ОПРЕДЕЛЯЕМ РЕКВИЗИТЫ
    if method == "usdt":
        details = USDT_DETAILS
        qr_path = USDT_QR_PATH
        send_photo = True
    elif method == "paypal":
        details = PAYPAL_DETAILS
        send_photo = False
    elif method == "alipay":
        details = ALIPAY_DETAILS
        qr_path = ALIPAY_QR_PATH
        send_photo = True

    # 3. ОТПРАВЛЯЕМ РЕКВИЗИТЫ
    if send_photo:
        try:
            photo_file = FSInputFile(qr_path)
            
            await bot.send_photo(
                chat_id=callback_query.message.chat.id,
                photo=photo_file,
                caption=f"**Payment Method: {method.upper()}**\n\n{details}\n\n[QR code for payment]",
                parse_mode="Markdown",
                reply_markup=confirm_and_back_keyboard
            )
        except FileNotFoundError:
            # Fallback if QR code is missing
            await bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=f"**Payment Method: {method.upper()}**\n\n{details}\n\n[Error: QR code file '{qr_path}' not found!]",
                parse_mode="Markdown",
                reply_markup=confirm_and_back_keyboard
            )
    else:
        # Send text-only details (for PayPal)
        # Обратите внимание, что мы отправляем PAYPAL_DETAILS, который уже содержит заголовок и жирный шрифт.
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"**Payment Method: {method.upper()}**\n\n{details}",
            parse_mode="Markdown",
            reply_markup=confirm_and_back_keyboard
        )

    await callback_query.answer()


# 4. I Paid button handler
@dp.callback_query(lambda c: c.data == 'confirm_payment')
async def process_confirm_payment(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(PaymentStates.waiting_for_screenshot)
    
    # Удаляем сообщение с реквизитами
    await bot.delete_message(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
    
    # Пытаемся удалить предыдущее сообщение (You have selected...)
    try:
        await bot.delete_message(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id - 1
        )
    except Exception:
        pass

    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text="Please **attach a screenshot** (photo) of the payment confirmation."
    )
    
    await callback_query.answer()


# 5. Screenshot handler
@dp.message(PaymentStates.waiting_for_screenshot)
async def process_screenshot(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("I am expecting a photo (screenshot). Please send the image.")
        return

    await state.clear()
    
    # Notify admin
    if ADMIN_ID != 0:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=message.photo[-1].file_id, 
            caption=f"❗️ **NEW PAYMENT RECEIVED** ❗️\n"
                    f"From user: @{message.from_user.username} (ID: {message.from_user.id})\n"
                    f"Please verify the payment screenshot.",
            parse_mode="Markdown"
        )
    
    # Send final message to user
    await message.answer(
        "✅ **Screenshot received.**\n\n"
        "My working hours are **9:00 AM – 8:00 PM (Indochina Time)**. Please wait for payment confirmation — once it’s confirmed, you’ll receive the guide right away."
    )


# =========================================================
#                       5. RUN
# =========================================================

async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True) 
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())