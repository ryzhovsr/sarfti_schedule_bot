import re

from aiogram import types, Dispatcher
from magic_filter import F
from user_actions import write_user_action
from message_editor import modify_message
from schedule_kb_handler import pressed_back_to_main
from create import bot, user_db, sch
import schedule_kb
import other_weeks_kb


async def pressed_back(callback: types.CallbackQuery):
    """Обработчик кнопки назад в клавиатуре с другими неделями"""
    await pressed_back_to_main(callback)


async def pressed_week(callback: types.CallbackQuery):
    """Обработчик кнопок выбора других недель"""
    current_selection = user_db.get_user_current_selection(callback.message.chat.id)
    selected_week = None

    for dic in callback.message.reply_markup.inline_keyboard:
        for item in dic:
            if item.callback_data == callback.data:
                # Регулярное выражение \d+$, которое соответствует одному или более цифрам в конце строки
                selected_week = re.search(r'\d+$', callback.data)
                if selected_week is not None:
                    selected_week = int(selected_week.group())
                break

    write_user_action(callback=callback, action=f"Посмотрел расписание по id недели {selected_week} для "
                                                f"{current_selection}")

    # Определяем группу или преподавателя
    if current_selection.endswith("."):
        current_schedule = sch.get_week_schedule_teacher(current_selection, selected_week)
    else:
        current_schedule = sch.get_week_schedule_group(current_selection, selected_week)

    last_message_id = user_db.get_last_message_id(callback.message.chat.id)

    try:
        await modify_message(bot, callback.message.chat.id, last_message_id, text=current_schedule,
                             reply_markup=schedule_kb.get_keyboard(selected_week=selected_week), parse_mode="Markdown")
    except RuntimeError:
        message_from_bot = await callback.message.answer(text=current_schedule,
                                                         reply_markup=schedule_kb.
                                                         get_keyboard(selected_week=selected_week),
                                                         parse_mode="Markdown")
        user_db.update_user_message_id(message_from_bot)


def register_callbacks_other_weeks_kb(dp: Dispatcher):
    dp.callback_query.register(pressed_back, other_weeks_kb.OtherWeeksFab.filter(F.action == "pressed_back"))
    dp.callback_query.register(pressed_week, other_weeks_kb.OtherWeeksFab.filter(F.action == "pressed_week"))
