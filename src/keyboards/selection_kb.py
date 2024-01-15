from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class SelectionFab(CallbackData, prefix="selFab"):
    """Фабрика колбэков для клавиатуры групп и ФИО преподаталей"""
    action: str
    value: Optional[str] = None


def get_selection_kb(groups_and_teachers_data):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    for arr in groups_and_teachers_data:
        for item, value in arr.items():
            builder.button(text=f"{value}", callback_data=SelectionFab(action="pressed_select", value=f"{value}"))

    builder.button(text="↩ Назад", callback_data=SelectionFab(action="pressed_back"))

    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()
