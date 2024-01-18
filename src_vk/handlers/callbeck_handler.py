from vkbottle.bot import Blueprint, MessageEvent
from vkbottle_types.events import GroupEventType
from src_vk.create import user_db, search_kb, sch
from src_vk.keyboards import start_kb, back_kb, main_kb, schedule_kb
from src_vk.scripts import message_editor

bp = Blueprint("Для обработки callback'ов")


@bp.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def message_event_handler(event: MessageEvent):
    """Отлов callback"""
    peer_id = event.peer_id
    message_id = user_db.get_last_message_id(peer_id)
    is_teacher = user_db.get_user_is_teacher(peer_id)
    current_selection = user_db.get_user_current_selection(peer_id)

    callback = list(event.payload.keys())[0]

    # Кнопки основного меню
    if callback == "main_menu":
        # Если нажата кнопка "Расписание на текущую неделю"
        if event.payload[callback] == "current_week":
            current_week_id = sch.get_current_week_id()
            text = sch.get_week_schedule_teacher(current_selection, current_week_id) if is_teacher \
                else sch.get_week_schedule_group(current_selection, current_week_id)
            await message_editor.edit_message(bp, peer_id, message_id, text, schedule_kb.get_keyboard())

    # Кнопки подменю
    if callback == "schedule":
        if event.payload[callback] == "time":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              schedule_kb.get_text_time(),
                                              schedule_kb.get_keyboard_after_press_time())

        if event.payload[callback] == "info":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              schedule_kb.get_text_info(),
                                              schedule_kb.get_keyboard_after_press_info())
        if event.payload[callback] == "back":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              main_kb.get_text(is_teacher, current_selection),
                                              main_kb.get_keyboard(peer_id))

    if callback == "current_selection":
        search_kb.delete_list_pages(peer_id)
        await message_editor.edit_message(bp, peer_id, message_id,
                                          main_kb.get_text(is_teacher, event.payload[callback]),
                                          main_kb.get_keyboard(peer_id))
        user_db.update_user_current_selection(peer_id, event.payload[callback])

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
                                              "👩‍🏫 Введите ФИО преподавателя:",
                                              back_kb.get_keyboard())
            user_db.update_user_is_teacher(peer_id, 1)

        # Если нажата кнопка "Студент"
        if event.payload[callback] == "student":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              "👨‍🎓 Введите название группы:",
                                              back_kb.get_keyboard())
            user_db.update_user_is_teacher(peer_id, 0)

        # Если нажата кнопка "Вернутся к выбору"
        if event.payload[callback] == "back":
            await message_editor.edit_message(bp, peer_id, message_id,
                                              await start_kb.get_text(bp, peer_id),
                                              start_kb.get_keyboard())
            user_db.update_user_is_teacher(peer_id, "NULL")
            user_db.update_user_current_selection(peer_id, "NULL")
