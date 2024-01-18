from vkbottle import Bot, VKAPIError
from vkbottle.bot import Blueprint


async def send_message(bot: Bot | Blueprint, peer_id, message, keyboard=None):
    try:
        await bot.api.messages.send(peer_id, random_id=0, message=message, keyboard=keyboard)
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)


async def edit_message(bot: Bot | Blueprint, peer_id, message_id, message, keyboard=None):
    try:
        await bot.api.messages.edit(peer_id, message_id=message_id, message=message, keyboard=keyboard)
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)


async def delete_message(bot: Bot | Blueprint, peer_id, message_id):
    try:
        await bot.api.messages.delete(peer_id=peer_id, message_ids=message_id, delete_for_all=True)
    except VKAPIError as e:
        print("Возникла ошибка:", e.code)


async def turn_page(bot: Bot | Blueprint, search_kb, peer_id, message_id, page_number):
    keyboard = search_kb.get_list_pages(peer_id)[page_number]
    await edit_message(bot, peer_id, message_id,
                       "Были найдены следующие совпадения 🔎",
                       keyboard)
