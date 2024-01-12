from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class GroupsTeachersCallbackFactory(CallbackData, prefix="fab"):
    """Фабрика колбэков для клавиатуры"""
    action: str = ""
    value: str = ""


def get_groups_teachers_fab(groups_and_teachers_data):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = InlineKeyboardBuilder()

    for dic in groups_and_teachers_data:
        for item, value in dic.items():
            builder.button(
                text=f"{value}",
                callback_data=GroupsTeachersCallbackFactory(value=f"item")
            )

    # Выравниваем кнопки по 4 в ряд, чтобы получилось 4 + 1
    builder.adjust(3)
    builder.button(text="Назад", callback_data=GroupsTeachersCallbackFactory(action="finish"))

    return builder.as_markup()

