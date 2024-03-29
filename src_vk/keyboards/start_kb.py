from vkbottle import Keyboard, Callback
from vkbottle.bot import Message, MessageEvent


def get_keyboard() -> str:
    """Возвращает клавиатуру начального меню"""
    return (Keyboard(inline=True)
            .add(Callback("👤 Преподавателя", {"start_menu": "teacher"})).row()
            .add(Callback("👥 Группы", {"start_menu": "student"}))
            ).get_json()


async def get_text(message_event: Message | MessageEvent) -> str:
    """Возвращает текст начального меню"""
    user = await message_event.ctx_api.users.get([message_event.peer_id])
    return f'Привет, {user[0].first_name}!👋\nКакое расписание хочешь получить?'
