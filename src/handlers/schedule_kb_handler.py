from aiogram import types, Dispatcher
from magic_filter import F

from src.create_bot import bot, user_db, sch
from src.message_editor import modify_message
from src.utils import add_sign_group_or_teacher
from src.keyboards import schedule_kb, main_kb
from src.handlers.main_kb_handler import pressed_current_week_sch


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с расписанием"""
    current_choice = user_db.get_user_current_choice(callback.message.chat.id)
    current_choice = add_sign_group_or_teacher(current_choice)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=current_choice,
                             reply_markup=main_kb.get_keyboard())
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=current_choice, reply_markup=main_kb.get_keyboard())
        user_db.update_user_message_id(message_from_bot)


async def pressed_time(callback: types.CallbackQuery):
    """Обработчик кнопки "Пары" в клавиатуре с расписанием"""
    text_out = "🕘 Расписание пар.\n\n" + \
               "🔹 *ПОНЕДЕЛЬНИК - ПЯТНИЦА:*\n"

    for item in sch.get_class_time_weekdays().items():
        match item[0]:
            case "1": text_out += u"\u0031\ufe0f\u20e3"
            case "2": text_out += u"\u0032\ufe0f\u20e3"
            case "3": text_out += u"\u0033\ufe0f\u20e3"
            case "4": text_out += u"\u0034\ufe0f\u20e3"
            case "5": text_out += u"\u0035\ufe0f\u20e3"
            case "6": text_out += u"\u0036\ufe0f\u20e3"
            case "7": text_out += u"\u0037\ufe0f\u20e3"

        text_out += " " + item[1] + "\n"

    text_out = text_out + "\n🔹 *СУББОТА:*\n"
    for item in sch.get_class_time_saturday().items():
        match item[0]:
            case "1": text_out += u"\u0031\ufe0f\u20e3"
            case "2": text_out += u"\u0032\ufe0f\u20e3"
            case "3": text_out += u"\u0033\ufe0f\u20e3"
            case "4": text_out += u"\u0034\ufe0f\u20e3"

        text_out += " " + item[1] + "\n"

        last_message_id = user_db.get_last_message_id(callback.message.chat.id)

        try:
            await modify_message(bot, callback.message.chat.id, last_message_id, text=text_out,
                                 reply_markup=schedule_kb.get_keyboard_after_press_time(),
                                 parse_mode="Markdown")
        except RuntimeError:
            message_from_bot = await callback.message.answer(text=text_out,
                                                             reply_markup=schedule_kb.get_keyboard_after_press_time(),
                                                             parse_mode="Markdown")
            user_db.update_user_message_id(message_from_bot)


async def pressed_info(callback: types.CallbackQuery):
    text_out = "Что означают значки в расписании занятий:\n\n" + \
               u"\u0031\ufe0f\u20e3 - номер пары\n" + \
               u"💬 - лекция\n" + \
               u"🔥 - практика, лаб. работа\n" + \
               u"📡 - онлайн\n" + \
               u"🅰 - подгруппа 1\n" + \
               u"🅱 - подгруппа 2"

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=text_out,
                             reply_markup=schedule_kb.get_keyboard_after_press_info())
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=text_out,
                                                         reply_markup=schedule_kb.get_keyboard_after_press_info())
        user_db.update_user_message_id(message_from_bot)


async def pressed_schedule(callback: types.CallbackQuery):
    await pressed_current_week_sch(callback)


def register_callbacks_schedule_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, schedule_kb.ScheduleFab.filter(F.action == "pressed_back"))
    dp.callback_query.register(pressed_time, schedule_kb.ScheduleFab.filter(F.action == "pressed_time"))
    dp.callback_query.register(pressed_info, schedule_kb.ScheduleFab.filter(F.action == "pressed_info"))
    dp.callback_query.register(pressed_schedule, schedule_kb.ScheduleFab.filter(F.action == "pressed_schedule"))
