from typing import Optional
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuGroupsTeachers(CallbackData, prefix="fab"):
    """Фабрика колбэков для клавиатуры"""
    action: str
    value: Optional[int] = None


def get_groups_teachers_fab(groups_and_teachers_data):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    for dic in groups_and_teachers_data:
        for item, value in dic.items():
            builder.button(
                text=f"{value}",
                callback_data=MenuGroupsTeachers(action="choice", value=f"{int(item)}")
            )

    builder.button(text="Назад", callback_data=MenuGroupsTeachers(action="go_to_back"))
    # Выравниваем кнопки по 2 в ряд
    builder.adjust(2)

    return builder.as_markup()
