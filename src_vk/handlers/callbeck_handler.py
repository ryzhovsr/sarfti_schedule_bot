from vkbottle.bot import MessageEvent, BotLabeler
from vkbottle_types.events import GroupEventType
from src_vk.create import user_db, search_kb, sch
from src_vk.keyboards import start_kb, back_kb, main_kb, schedule_kb, notification_kb
from src_vk.scripts import message_editor

labeler = BotLabeler()


@labeler.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
async def message_event_handler(event: MessageEvent):
    """Функция, которая отслеживает callback'и"""
    # Смотрим, кто нажал на кнопку и вытаскиваем его из БД
    peer_id = event.peer_id
    message_id = user_db.get_last_message_id(peer_id)
    is_teacher = user_db.get_user_is_teacher(peer_id)
    current_selection = user_db.get_user_current_selection(peer_id)

    # Смотрим callback кнопки
    callback = list(event.payload.keys())[0]

    # Кнопки основного меню
    if callback == "main_menu":
        # Если нажата кнопка "Расписание на текущую неделю"
        if event.payload[callback] == "current_week":
            current_week_id = sch.get_current_week_id()
            text = sch.get_week_schedule_teacher(current_selection, current_week_id) if is_teacher \
                else sch.get_week_schedule_group(current_selection, current_week_id)

            await message_editor.edit_message(event, message_id, text, schedule_kb.get_keyboard())

        # Если нажата кнопка "Расписание на другие недели"
        if event.payload[callback] == "other_week":
            dict_weeks = sch.get_upcoming_weeks_list()
            # Если на следующую неделю нет расписания
            if len(dict_weeks) == 0:
                await event.show_snackbar("Расписания на след. неделю не опубликовано 😕")
            else:
                await message_editor.edit_message(event, message_id,
                                                  "Доступны след. недели 🔎",
                                                  schedule_kb.get_keyboard_next_week(dict_weeks))

        # Если нажата кнопка "Уведомления"
        if event.payload[callback] == "notifications":
            await message_editor.edit_message(event, message_id,
                                              "Выберете уведомления",
                                              notification_kb.get_keyboard(peer_id))

    # Кнопки меню уведомлений
    if callback == "notifications_menu":
        # Если нажата кнопка "Изменения на текущей неделе"
        if event.payload[callback] == "current_week_change":
            user_db.update_is_note_current_week_changes(peer_id, not user_db.get_user_notification(peer_id)[0])
            await message_editor.edit_message(event, message_id,
                                              "Выберете уведомления",
                                              notification_kb.get_keyboard(peer_id))

        # Если нажата кнопка "Появилось новое расписание"
        if event.payload[callback] == "sch_next_week":
            user_db.update_is_note_new_schedule(peer_id, not user_db.get_user_notification(peer_id)[1])
            await message_editor.edit_message(event, message_id,
                                              "Выберете уведомления",
                                              notification_kb.get_keyboard(peer_id))

        # Если нажата кнопка "Закрыть уведомление"
        if event.payload[callback] == "close":
            if current_selection != "NULL":
                await message_editor.edit_message(event, message_id,
                                                  main_kb.get_text(is_teacher, current_selection),
                                                  main_kb.get_keyboard(peer_id))
            else:
                await message_editor.edit_message(event, message_id,
                                                  await start_kb.get_text(event),
                                                  start_kb.get_keyboard())

    # Кнопки подменю расписания
    if callback == "schedule":
        # Если нажата кнопка "Пары"
        if event.payload[callback] == "time":
            await message_editor.edit_message(event, message_id,
                                              schedule_kb.get_text_time(),
                                              schedule_kb.get_keyboard_after_press_time())

        # Если нажата кнопка "Информация"
        if event.payload[callback] == "info":
            await message_editor.edit_message(event, message_id,
                                              schedule_kb.get_text_info(),
                                              schedule_kb.get_keyboard_after_press_info())

        # Если нажата кнопка "Вернуться в меню"
        if event.payload[callback] == "back":
            await message_editor.edit_message(event, message_id,
                                              main_kb.get_text(is_teacher, current_selection),
                                              main_kb.get_keyboard(peer_id))

    # Кнопки перехода по страницам
    if callback == "search_menu":
        # Если нажата кнопка "Следующая"
        if event.payload[callback] == "following":
            search_kb.set_page_number(peer_id, search_kb.get_page_number(peer_id) + 1)

            await message_editor.turn_page(event, search_kb, message_id, search_kb.get_page_number(peer_id))

        # Если нажата кнопка "Предыдущая"
        if event.payload[callback] == "previous":
            search_kb.set_page_number(peer_id, search_kb.get_page_number(peer_id) - 1)

            await message_editor.turn_page(event, search_kb, message_id, search_kb.get_page_number(peer_id))

    # Кнопки начального меню
    if callback == "start_menu":
        # Если нажата кнопка "Преподаватель"
        if event.payload[callback] == "teacher":
            await message_editor.edit_message(event, message_id,
                                              "👤 Введите фамилию преподавателя:\n(Можно ввести первые символы)",
                                              back_kb.get_keyboard())

            user_db.update_user_is_teacher(peer_id, 1)

        # Если нажата кнопка "Студент"
        if event.payload[callback] == "student":
            await message_editor.edit_message(event, message_id,
                                              "👥 Введите название группы:\n(Можно ввести первые символы)",
                                              back_kb.get_keyboard())

            user_db.update_user_is_teacher(peer_id, 0)

        # Если нажата кнопка "Вернутся к выбору"
        if event.payload[callback] == "back":
            await message_editor.edit_message(event, message_id,
                                              await start_kb.get_text(event),
                                              start_kb.get_keyboard())

            # Обнуляем БД
            user_db.update_user_is_teacher(peer_id, "NULL")
            user_db.update_user_current_selection(peer_id, "NULL")

    # Если пользователь выберет группу/преподавателя
    if callback == "current_selection":
        search_kb.delete_list_pages(peer_id)

        await message_editor.edit_message(event, message_id,
                                          main_kb.get_text(is_teacher, event.payload[callback]),
                                          main_kb.get_keyboard(peer_id))

        user_db.update_user_current_selection(peer_id, event.payload[callback])

    # Если пользователь выберет неделю
    if callback == "week_selection":
        week = event.payload["week_selection"]
        text = sch.get_week_schedule_teacher(current_selection, week) if is_teacher \
            else sch.get_week_schedule_group(current_selection, week)

        await message_editor.edit_message(event, message_id, text, schedule_kb.get_keyboard())
