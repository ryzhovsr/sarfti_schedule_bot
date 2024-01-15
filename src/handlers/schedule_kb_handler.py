from aiogram import types, Dispatcher
from magic_filter import F

from create_bot import bot, user_db
from message_editor import modify_message
from utils import add_sign_group_or_teacher
from keyboards import schedule_kb, main_kb


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с расписанием"""
    current_choise = user_db.get_user_current_choice(callback.message.chat.id)
    current_choise = add_sign_group_or_teacher(current_choise)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=current_choise,
                             reply_markup=main_kb.get_keyboard())
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=current_choise, reply_markup=main_kb.get_keyboard())
        user_db.update_user_message_id(message_from_bot)


def register_callbacks_schedule_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, schedule_kb.ScheduleFab.filter(F.action == "pressed_back"))
