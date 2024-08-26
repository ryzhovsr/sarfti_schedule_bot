from vkbottle import Keyboard, Callback

from src_vk.create import user_db


def get_keyboard(user_id: int) -> str:
    """Возвращает клавиатуру уведомлений"""
    keyboard = Keyboard(inline=True)

    notifications = user_db.get_user_notification(user_id)

    if notifications[0]:
        keyboard.add(
            Callback("🔔 Изменения текущей недели", {"notifications_menu": "current_week_change"})).row()
    else:
        keyboard.add(
            Callback("🔕 Изменения текущей недели", {"notifications_menu": "current_week_change"})).row()

    if notifications[1]:
        keyboard.add(Callback("🔔 Новое расписание", {"notifications_menu": "sch_next_week"})).row()
    else:
        keyboard.add(Callback("🔕 Новое расписание", {"notifications_menu": "sch_next_week"})).row()

    keyboard.add(Callback("↩ Вернуться в меню", {"schedule": "back"}))

    return keyboard.get_json()


def get_close_kb() -> str:
    """Возвращает клавиатуру с кнопкой закрыть уведомление"""
    return (Keyboard(inline=True)
            .add(Callback("Закрыть уведомление", {"notifications_menu": "close"}))
            ).get_json()
