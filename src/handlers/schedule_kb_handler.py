from aiogram import types, Dispatcher
from magic_filter import F

from src.create_bot import bot, user_db, sch
from src.message_editor import modify_message
from src.utils import add_sign_group_or_teacher
from src.keyboards import schedule_kb, main_kb


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


async def pressed_time(callback: types.CallbackQuery):
    """Обработчик кнопки пары в клавиатуре с расписанием"""
    text_out = '🕘 Расписание пар.\n\n' + \
               '🔹 *ПОНЕДЕЛЬНИК - ПЯТНИЦА:*\n'
    for item in sch.get_class_time_weekdays().items():
        if '1' in item[0]:
            text_out = text_out + u'\u0031\ufe0f\u20e3'
        if '2' in item[0]:
            text_out = text_out + u'\u0032\ufe0f\u20e3'
        if '3' in item[0]:
            text_out = text_out + u'\u0033\ufe0f\u20e3'
        if '4' in item[0]:
            text_out = text_out + u'\u0034\ufe0f\u20e3'
        if '5' in item[0]:
            text_out = text_out + u'\u0035\ufe0f\u20e3'
        if '6' in item[0]:
            text_out = text_out + u'\u0036\ufe0f\u20e3'
        if '7' in item[0]:
            text_out = text_out + u'\u0037\ufe0f\u20e3'
        if '8' in item[0]:
            text_out = text_out + u'\u0038\ufe0f\u20e3'
        if '9' in item[0]:
            text_out = text_out + u'\u0039\ufe0f\u20e3'
        text_out = text_out + ' ' + item[1] + '\n'

    text_out = text_out + '\n🔹 *СУББОТА:*\n'
    for item in sch.get_class_time_saturday().items():
        if '1' in item[0]:
            text_out = text_out + u'\u0031\ufe0f\u20e3'
        if '2' in item[0]:
            text_out = text_out + u'\u0032\ufe0f\u20e3'
        if '3' in item[0]:
            text_out = text_out + u'\u0033\ufe0f\u20e3'
        if '4' in item[0]:
            text_out = text_out + u'\u0034\ufe0f\u20e3'
        if '5' in item[0]:
            text_out = text_out + u'\u0035\ufe0f\u20e3'
        if '6' in item[0]:
            text_out = text_out + u'\u0036\ufe0f\u20e3'
        if '7' in item[0]:
            text_out = text_out + u'\u0037\ufe0f\u20e3'
        if '8' in item[0]:
            text_out = text_out + u'\u0038\ufe0f\u20e3'
        if '9' in item[0]:
            text_out = text_out + u'\u0039\ufe0f\u20e3'
        text_out = text_out + ' ' + item[1] + '\n'


def register_callbacks_schedule_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, schedule_kb.ScheduleFab.filter(F.action == "pressed_back"))
    dp.callback_query.register(pressed_time, schedule_kb.ScheduleFab.filter(F.action == "pressed_time"))

