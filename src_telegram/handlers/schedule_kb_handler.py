import re

from aiogram import types, Dispatcher
from magic_filter import F
from src_telegram.create import bot, user_db, sch
from src_telegram.scripts.message_editor import modify_message
from schedule.utils import add_sign_group_or_teacher, write_user_action
from src_telegram.keyboards import schedule_kb, main_kb
from src_telegram.handlers.main_kb_handler import pressed_current_week_sch, pressed_other_week_sch


async def pressed_back_to_main(callback: types.CallbackQuery):
    """Обработчик кнопки назад в меню в клавиатуре с расписанием"""
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


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с расписанием"""
    await pressed_other_week_sch(callback)


async def pressed_time(callback: types.CallbackQuery):
    """Обработчик кнопки "Пары" в клавиатуре с расписанием"""
    write_user_action(callback=callback, action="Нажал кнопку 'Пары'")
    text_out = "🕘 Расписание пар.\n\n" + \
               "🔹 *ПОНЕДЕЛЬНИК - ПЯТНИЦА:*\n"

    one = u"\u0031\ufe0f\u20e3"
    two = u"\u0032\ufe0f\u20e3"
    three = u"\u0033\ufe0f\u20e3"
    four = u"\u0034\ufe0f\u20e3"
    five = u"\u0035\ufe0f\u20e3"
    six = u"\u0036\ufe0f\u20e3"
    seven = u"\u0037\ufe0f\u20e3"

    for item in sch.get_class_time_weekdays().items():
        match item[0]:
            case "1": text_out += one
            case "2": text_out += two
            case "3": text_out += three
            case "4": text_out += four
            case "5": text_out += five
            case "6": text_out += six
            case "7": text_out += seven

        text_out += " " + item[1] + "\n"

    text_out += "\n🔹 *СУББОТА:*\n"

    for item in sch.get_class_time_saturday().items():
        match item[0]:
            case "1": text_out += one
            case "2": text_out += two
            case "3": text_out += three
            case "4": text_out += four

        text_out += " " + item[1] + "\n"

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    selected_week = None

    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                # Регулярное выражение \d+$, которое соответствует одному или более цифрам в конце строки
                selected_week = re.search(r'\d+$', callback.data)
                if selected_week is not None:
                    selected_week = int(selected_week.group())
                break

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=text_out,
                             reply_markup=schedule_kb.get_keyboard_after_press_time(selected_week=selected_week),
                             parse_mode="Markdown")
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=text_out,
                                                         reply_markup=schedule_kb.
                                                         get_keyboard_after_press_time(selected_week=selected_week),
                                                         parse_mode="Markdown")
        user_db.update_user_message_id(message_from_bot)


async def pressed_info(callback: types.CallbackQuery):
    """Обработчик кнопки "Информация" в клавиатуре с расписанием"""
    write_user_action(callback=callback, action="Нажал кнопку 'Информация'")
    text_out = "Что означают значки в расписании занятий:\n\n" + \
               u"\u0031\ufe0f\u20e3 - номер пары\n" + \
               "💬 - лекция\n" + \
               "🔥 - практика, лаб. работа\n" + \
               "📡 - онлайн\n" + \
               "🅰 - подгруппа 1\n" + \
               "🅱 - подгруппа 2"

    selected_week = None

    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                # Регулярное выражение \d+$, которое соответствует одному или более цифрам в конце строки
                selected_week = re.search(r'\d+$', callback.data)
                if selected_week is not None:
                    selected_week = int(selected_week.group())
                break

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id,
                             text=text_out,
                             reply_markup=schedule_kb.get_keyboard_after_press_info(selected_week=selected_week))
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=text_out,
                                                         reply_markup=schedule_kb.
                                                         get_keyboard_after_press_info(selected_week=selected_week))
        user_db.update_user_message_id(message_from_bot)


async def pressed_schedule(callback: types.CallbackQuery):
    await pressed_current_week_sch(callback)


async def pressed_other_schedule(callback: types.CallbackQuery):
    selected_week_id = None

    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                # Регулярное выражение \d+$, которое соответствует одному или более цифрам в конце строки
                selected_week_id = re.search(r'\d+$', callback.data)
                if selected_week_id is not None:
                    selected_week_id = int(selected_week_id.group())
                break

    current_selection = user_db.get_user_current_selection(callback.message.chat.id)

    # Определяем группу или преподавателя
    if current_selection.endswith("."):
        schedule = sch.get_week_schedule_teacher(current_selection, selected_week_id)
    else:
        schedule = sch.get_week_schedule_group(current_selection, selected_week_id)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=schedule,
                             reply_markup=schedule_kb.get_keyboard(selected_week_id), parse_mode="Markdown")
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=schedule,
                                                         reply_markup=schedule_kb.get_keyboard(selected_week_id),
                                                         parse_mode="Markdown")
        user_db.update_user_message_id(message_from_bot)


def register_callbacks_schedule_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back_to_main, schedule_kb.ScheduleFab.filter(F.action == "pressed_back_to_main"))
    dp.callback_query.register(pressed_time, schedule_kb.ScheduleFab.filter(F.action == "pressed_time"))
    dp.callback_query.register(pressed_info, schedule_kb.ScheduleFab.filter(F.action == "pressed_info"))
    dp.callback_query.register(pressed_schedule, schedule_kb.ScheduleFab.filter(F.action == "pressed_schedule"))
    dp.callback_query.register(pressed_back, schedule_kb.ScheduleFab.filter(F.action == "pressed_back"))
    dp.callback_query.register(pressed_other_schedule,
                               schedule_kb.ScheduleFab.filter(F.action == "pressed_other_schedule"))
