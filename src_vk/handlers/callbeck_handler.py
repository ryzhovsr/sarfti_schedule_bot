from vkbottle.bot import Blueprint, MessageEvent
from vkbottle_types.events import GroupEventType
from src_vk.create import user_db, search_kb
from src_vk.keyboards import start_kb, back_kb
from src_vk.scripts import message_editor

bp = Blueprint("Для обработки callback'ов")


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def message_event_handler(event: MessageEvent):
    """Отлов callback"""
    # Получаем id пользователя
    peer_id = event.peer_id
    # Получаем id последнего сообщения бота
    message_id = user_db.get_last_message_id(peer_id)

    callback = list(event.payload.keys())[0]

    if callback == "info":
        if event.payload[callback] == "info":
            await event.show_snackbar("Ботик находится в разработке🙃")

    if callback == "current_selection":
        # TODO: реализовать удаление в словаре
        await message_editor.edit_message(bp, peer_id, message_id,
                                          f"Вы выбрали {event.payload[callback]}:",
                                          back_kb.get_keyboard())

    # Кнопки перехода по страницам
    if callback == "search_menu":
        # Если нажата кнопка "Следующая"
        if event.payload[callback] == "following":
            search_kb.set_page_number(peer_id, search_kb.get_page_number(peer_id) + 1)
            await message_editor.turn_page(bp, search_kb, peer_id, message_id, search_kb.get_page_number(peer_id))

        # Если нажата кнопка "Предыдущая"
        if event.payload[callback] == "previous":
            search_kb.set_page_number(peer_id, search_kb.get_page_number(peer_id) - 1)
            await message_editor.turn_page(bp, search_kb, peer_id, message_id, search_kb.get_page_number(peer_id))

    # Кнопки начального меню
    if callback == "start_menu":

        # Если нажата кнопка "Преподаватель"
        if event.payload[callback] == "teacher":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              "Введите ФИО преподавателя:",
                                              back_kb.get_keyboard())
            user_db.update_user_is_teacher(peer_id, 1)

        # Если нажата кнопка "Студент"
        if event.payload[callback] == "student":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              "Введите название группы:",
                                              back_kb.get_keyboard())
            user_db.update_user_is_teacher(peer_id, 0)

        # Если нажата кнопка "Вернутся к выбору"
        if event.payload[callback] == "back":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              await start_kb.get_text(bp, peer_id),
                                              start_kb.get_keyboard())
            user_db.update_user_is_teacher(peer_id, "NULL")
