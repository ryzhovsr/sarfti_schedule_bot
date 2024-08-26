from vkbottle import VKAPIError
from vkbottle.bot import Message, MessageEvent


async def send_message(message_event: Message | MessageEvent, message: str, keyboard: str = None):
    """Отправляет сообщение пользователю"""
    try:
        await message_event.ctx_api.messages.send(message_event.peer_id, random_id=0, message=message,
                                                  keyboard=keyboard)
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)


async def edit_message(message_event: Message | MessageEvent, message_id: int, message: str, keyboard: str = None):
    """Редактирует сообщение бота"""
    try:
        await message_event.ctx_api.messages.edit(message_event.peer_id, message_id=message_id, message=message,
                                                  keyboard=keyboard)
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)


async def delete_message(message_event: Message | MessageEvent, message_id: int):
    """Удаляет сообщение бота"""
    try:
        await message_event.ctx_api.messages.delete(peer_id=message_event.peer_id, message_ids=[message_id],
                                                    delete_for_all=True)
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)
        await delete_by_edit_message(message_event, message_id)


async def delete_by_edit_message(message_event: Message | MessageEvent, message_id: int):
    """Редактирует сообщение, оставляя пустоту"""
    try:
        await edit_message(message_event, message_id, "ㅤ")
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)


async def turn_page(message_event: Message | MessageEvent, search_kb, message_id, page_number):
    """Переворачивает страницу книжки поиска"""
    await edit_message(message_event, message_id,
                       "Были найдены следующие совпадения 🔎",
                       search_kb.get_list_pages(message_event.peer_id)[page_number])
