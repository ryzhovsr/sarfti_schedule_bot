from aiogram import types, Dispatcher
from magic_filter import F

from src.create_bot import bot, user_db
from src.message_editor import modify_message
from src.utils import add_sign_group_or_teacher
from src.keyboards import notification_kb, main_kb


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад на клавиатуре с уведомлениями"""
    current_selection = user_db.get_user_current_selection(callback.message.chat.id)
    current_selection = add_sign_group_or_teacher(current_selection)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=current_selection,
                             reply_markup=main_kb.get_keyboard(callback.message.chat.id))
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=current_selection,
                                                         reply_markup=main_kb.get_keyboard(callback.message.chat.id))
        user_db.update_user_message_id(message_from_bot)


def register_callbacks_schedule_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, notification_kb.NotificationsFab.filter(F.action == "pressed_back"))
