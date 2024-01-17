from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class OtherWeeksFab(CallbackData, prefix="othWeekFab"):
    """Фабрика колбэков для клавиатуры групп и ФИО преподавателей"""
    action: str
    value: Optional[str] = None


def get_keyboard(upcoming_weeks: list):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    for item in upcoming_weeks:
        builder.button(text=f"{item}", callback_data=OtherWeeksFab(action="pressed_select", value=f"{item}"))

    builder.button(text="↩ Вернуться в меню",callback_data=OtherWeeksFab(action="pressed_back"))

    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()
