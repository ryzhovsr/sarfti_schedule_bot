from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Optional


class ScheduleFab(CallbackData, prefix="schFab"):
    """Фабрика колбэков для расписания"""
    action: str
    selected_week: Optional[int] = None


def get_keyboard(selected_week: int = None):
    builder = InlineKeyboardBuilder()

    builder.button(text="❓Информация", callback_data=ScheduleFab(action="pressed_info", selected_week=selected_week))
    builder.button(text="🕘 Пары", callback_data=ScheduleFab(action="pressed_time", selected_week=selected_week))

    if selected_week is not None:
        builder.button(text="⬅️ Назад", callback_data=ScheduleFab(action="pressed_back", selected_week=selected_week))

    builder.button(text="↩ Вернуться в меню", callback_data=ScheduleFab(action="pressed_back_to_main"))

    builder.adjust(2)

    return builder.as_markup()


def get_keyboard_after_press_time(selected_week: int = None):
    builder = InlineKeyboardBuilder()

    builder.button(text="❓Информация", callback_data=ScheduleFab(action="pressed_info", selected_week=selected_week))

    if selected_week is not None:
        builder.button(text="🔼 Расписание", callback_data=ScheduleFab(action="pressed_other_schedule",
                                                                      selected_week=selected_week))
        builder.button(text="⬅️ Назад", callback_data=ScheduleFab(action="pressed_back", selected_week=selected_week))
    else:
        builder.button(text="🔼 Расписание",
                       callback_data=ScheduleFab(action="pressed_schedule", selected_week=selected_week))

    builder.button(text="↩ Вернуться в меню", callback_data=ScheduleFab(action="pressed_back_to_main"))

    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()


def get_keyboard_after_press_info(selected_week: int = None):
    builder = InlineKeyboardBuilder()

    # Определяем что обрабатывать при нажатии на кнопку - расписание на текущую неделю или на другие
    if selected_week is not None:
        builder.button(text="🔼 Расписание",
                       callback_data=ScheduleFab(action="pressed_other_schedule", selected_week=selected_week))
    else:
        builder.button(text="🔼 Расписание",
                       callback_data=ScheduleFab(action="pressed_schedule", selected_week=selected_week))

    builder.button(text="🕘 Пары", callback_data=ScheduleFab(action="pressed_time", selected_week=selected_week))

    if selected_week is not None:
        builder.button(text="⬅️ Назад", callback_data=ScheduleFab(action="pressed_back", selected_week=selected_week))

    builder.button(text="↩ Вернуться в меню", callback_data=ScheduleFab(action="pressed_back_to_main"))

    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()
