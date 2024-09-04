from aiogram import types, Dispatcher
from magic_filter import F

from create import bot, user_db
from message_editor import modify_message
from utils import add_sign_group_or_teacher
import selection_kb
import main_menu_kb


async def pressed_select(callback: types.CallbackQuery):
    """Обработчик кнопок выбора группы/ФИО преподавателя"""
    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    # Текст кнопки, на которую нажал пользователь
    current_selection = ''

    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                current_selection = item.text
                break

    user_db.update_user_current_selection(callback.message.chat.id, current_selection)
    text = add_sign_group_or_teacher(current_selection)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=text,
                             reply_markup=main_menu_kb.get_keyboard(callback.message.chat.id))
    except RuntimeError:
        # Если не получилось отредактировать - отправляем новое и записываем его в БД
        message_from_bot = await callback.message.answer(text=text,
                                                         reply_markup=main_menu_kb.get_keyboard(callback.message.chat.id))
        user_db.update_user_message_id(message_from_bot)


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре выбора группы/ФИО преподавателя"""
    # Получаем id последнего сообщения у пользователя
    last_message_id = user_db.get_last_message_id(callback.message.chat.id)
    text = (f"Введите название группы / фамилию преподавателя.\n"
            f"(Можно ввести первые символы)")

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text)
    except RuntimeError:
        message_from_bot = await callback.message.answer(text)
        user_db.update_user_message_id(message_from_bot)


def register_selection_callbacks(dp: Dispatcher):
    dp.callback_query.register(pressed_select, selection_kb.SelectionFab.filter(F.action == "pressed_select"))
    dp.callback_query.register(pressed_back, selection_kb.SelectionFab.filter(F.action == "pressed_back"))
