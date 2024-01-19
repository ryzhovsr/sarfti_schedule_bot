from vkbottle import Keyboard, Callback

from src_vk.create import user_db


def get_keyboard(user_id: int) -> str:
    """Возвращает клавиатуру основного меню"""
    keyboard = (Keyboard(inline=True)
                .add(Callback("🔼 Расписание на текущую неделю", {"main_menu": "current_week"})).row()
                .add(Callback("📅 Расписание на другие недели", {"main_menu": "other_week"})).row())

    if user_db.is_user_notification_enabled(user_id):
        keyboard.add(Callback("🔔 Уведомления [вкл]", {"main_menu": "notifications"})).row()

    else:
        keyboard.add(Callback("🔕 Уведомления [выкл]", {"main_menu": "notifications"})).row()

    keyboard.add(Callback("↩ Назад", {"start_menu": "back"}))

    return keyboard.get_json()


def get_text(is_teacher: int, current_selection: str) -> str:
    """Возвращаем текст, относительно от выбора пользователя"""
    return ("👩‍🏫 Преподаватель " if is_teacher == 1 else "👨‍🎓 Группа ") + current_selection
