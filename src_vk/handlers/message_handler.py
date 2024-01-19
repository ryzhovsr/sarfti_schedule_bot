from vkbottle.bot import Message, BotLabeler

from schedule.utils import find_coincidence_group_teacher, add_dash_in_group
from src_vk.create import user_db, sch, search_kb
from src_vk.keyboards import start_kb, back_kb, main_kb
from src_vk.scripts import message_editor

labeler = BotLabeler()

labeler.vbml_ignore_case = True


@labeler.private_message(text=["Начать", "/start", "Привет", "Хай", "start", "/reset", "reset"])
async def start_handler(message: Message):
    """Обработчик начальных сообщений"""
    # Если пользователь существует в базе данных удаляем прошлое сообщение
    if user_db.is_user_exists(message.peer_id) is not None:
        await message_editor.delete_message(message, user_db.get_last_message_id(message.peer_id))

    message_from_bot = await message.answer(message=await start_kb.get_text(message),
                                            keyboard=start_kb.get_keyboard())
    # Обновляем БД
    user_db.update_user_message_id(message_from_bot)
    user_db.update_user_is_teacher(message.peer_id, "NULL")
    user_db.update_user_current_selection(message.peer_id, "NULL")


@labeler.private_message()
async def message_handler(message: Message):
    """Обработчик всех сообщений"""
    # Смотрим, кто прислал сообщение и вытаскиваем его из БД
    peer_id = message.peer_id
    is_teacher = user_db.get_user_is_teacher(peer_id)
    message_id = user_db.get_last_message_id(peer_id)
    # Если пользователь написал группу слитно, то образуем текст
    text = message.text if is_teacher else add_dash_in_group(message.text)

    # Если пользователь не выбрал, кого искать, то игнорируем его сообщения
    if is_teacher != "NULL":
        coincidence = find_coincidence_group_teacher(text, sch)

        await message_editor.delete_message(message, message_id)

        # Если есть совпадение, то выводим их пользователю
        if len(coincidence[is_teacher]) != 0:
            keyboard = search_kb.get_keyboard(peer_id, coincidence[is_teacher])[0]

            # Если совпадение только одно, то выводим основное меню
            if len(coincidence[is_teacher]) == 1:
                search_kb.delete_list_pages(peer_id)
                current_selection = keyboard.buttons[0][0].action.label
                message_from_bot = await message.answer(message=main_kb.get_text(is_teacher, current_selection),
                                                        keyboard=main_kb.get_keyboard(peer_id))

                user_db.update_user_current_selection(peer_id, current_selection)

            else:
                message_from_bot = await message.answer(message="Были найдены следующие совпадения 🔎",
                                                        keyboard=keyboard)

            user_db.update_user_message_id(message_from_bot)

        # Если нет совпадений, сообщаем об этом пользователю
        else:
            message_from_bot = await message.answer(message=back_kb.get_text(is_teacher),
                                                    keyboard=back_kb.get_keyboard())

            user_db.update_user_message_id(message_from_bot)
