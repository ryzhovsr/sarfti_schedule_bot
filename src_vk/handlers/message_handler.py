from vkbottle.bot import Blueprint, Message

from src_telegram.scripts.utils import find_coincidence_group_teacher
from src_vk.create import user_db, sch, search_kb
from src_vk.keyboards import start_kb, back_kb
from src_vk.scripts import message_editor

bp = Blueprint("Для обработки сообщений")

bp.on.vbml_ignore_case = True


@bp.on.private_message(text=["Начать", "/start", "Привет"])
async def start_handler(message: Message):
    """Обработчик начальных сообщений"""
    message_from_bot = await message.answer(message=await start_kb.get_text(bp, message.peer_id),
                                            keyboard=start_kb.get_keyboard())
    # Обновляем id последнего сообщения у пользователя
    user_db.update_user_message_id(message_from_bot)


@bp.on.private_message()
async def message_handler(message: Message):
    """Обработчик всех сообщений"""
    peer_id = message.peer_id
    coincidence = await find_coincidence_group_teacher(message.text, sch)
    is_teacher = user_db.get_is_teacher(peer_id)
    message_id = user_db.get_last_message_id(peer_id)

    if is_teacher is not None:
        # Удаляем последнее сообщение если это возможно
        await message_editor.delete_message(bp, peer_id, message_id)
        # Если есть совпадение, то выводим их пользователю
        if len(coincidence[is_teacher]) != 0:
            keyboard = search_kb.get_keyboard(peer_id, coincidence[is_teacher])[0]
            if len(keyboard.buttons) == 2:
                current_selection = keyboard.buttons[0][0].action.label
                message_from_bot = await message.answer(message=f"Выбрали {current_selection}",
                                                        keyboard=back_kb.get_keyboard())
            else:
                message_from_bot = await message.answer(message="Были найдены следующие совпадения:",
                                                        keyboard=keyboard)
            user_db.update_user_message_id(message_from_bot)

        else:
            message_from_bot = await message.answer(message=back_kb.get_text(is_teacher),
                                                    keyboard=back_kb.get_keyboard())
            user_db.update_user_message_id(message_from_bot)
