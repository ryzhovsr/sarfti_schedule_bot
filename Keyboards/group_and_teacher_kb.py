from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class KeyboardGroupsTeachers(CallbackData, prefix="fab"):
    """Фабрика колбэков для клавиатуры групп и ФИО преподаталей"""
    action: str
    value: Optional[int] = None


def get_keyboard(groups_and_teachers_data):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    for arr in groups_and_teachers_data:
        for item, value in arr.items():
            builder.button(text=f"{value}", callback_data=KeyboardGroupsTeachers(action="pressed_select",
                                                                                 value=f"{int(item)}"))

    builder.button(text="↩ Назад", callback_data=KeyboardGroupsTeachers(action="pressed_go_back"))
    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()