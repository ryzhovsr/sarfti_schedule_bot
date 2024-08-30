"""Модуль содержит клавиатуру основного меню"""

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telebot.types import InlineKeyboardMarkup
from create import user_db


class MainFab(CallbackData, prefix="mainFab"):
    """Фабрика колбэков для основной клавиатуры"""
    action: str


def get_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Возвращает клавиатуру основного меню"""
    builder = InlineKeyboardBuilder()

    builder.button(text="🔼 Расписание на текущую неделю", callback_data=MainFab(action="pressed_current_week_sch"))
    builder.button(text="Расписание на другие недели", callback_data=MainFab(action="pressed_other_week_sch"))

    # Устанавливаем эмодзи уведомления, в зависимости от выбора пользователя
    if user_db.is_user_notification_enabled(user_id):
        emoji = "🔔"
    else:
        emoji = "🔕"

    builder.button(text=f"{emoji} Уведомления [выкл]", callback_data=MainFab(action="pressed_notifications"))
    builder.button(text="Закрыть", callback_data=MainFab(action="pressed_back"))

    # Выравниваем кнопки по 1 в ряд
    builder.adjust(1)

    # Возвращаем готовый объект клавиатуры
    return builder.as_markup()
