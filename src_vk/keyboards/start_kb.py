from vkbottle import Keyboard, Callback
from vkbottle.bot import Bot, Blueprint


def get_keyboard():
    """Возвращает клавиатуру начального меню"""
    return (Keyboard(inline=True)
            .add(Callback("👩‍🏫 Преподавателя", {"start_menu": "teacher"}))
            .add(Callback("👨‍🎓 Студента", {"start_menu": "student"}))
            .row()
            .add(Callback("Инфо", {"info": "info"}))
            ).get_json()


async def get_text(bot: Bot | Blueprint, peer_id):
    """Возвращает текст начального меню"""
    user = await bot.api.users.get(peer_id)
    return f'Привет, {user[0].first_name} {user[0].last_name}!👋\n Какое расписание хочешь получить?'
