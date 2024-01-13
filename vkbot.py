from vkbottle import Keyboard, Callback, GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from schedule_data import ScheduleData
from utils import find_coincidence_group_teacher
from vk_userdb import UserDatabase

token = "vk1.a.j8Yt1zZf7KLV75zluh9yXUmfoqE_lbgWZzX9xZaHgvm6kO8C96_ah-l7NXqBakFgzimC8AuMw0Fq0M4KbGQFUjzLrT3DtsFW8yHtdTSWbZY9JP2OhF12OVUwLVN_7ddkj7yxQdNFh-pgatYgWLzSvcA-2SrnG04jvADcNMmg-eUSEXW3j9kEmu3unAwnx2JcrqnY0DgpV1bmyzWEIFRoLA"
bot = Bot(token)
sch = ScheduleData()
user_db = UserDatabase()


# Перенести в отдельный модуль
async def initial_menu_keyboard(user_id):
    """Возвращает клавиатуру начальное меню"""
    user = await bot.api.users.get(user_id)

    keyboard = (
        Keyboard(inline=True)
        .add(Callback("Преподавателя", {"initial_menu": "teacher"}))
        .add(Callback("Студента", {"initial_menu": "student"}))
        .row()
        .add(Callback("Инфо", {"info": "info"}))
    ).get_json()

    text = f'Привет, {user[0].first_name} {user[0].last_name}!👋\n Какое расписание хочешь получить?'

    return keyboard, text


def search_menu_keyboard(coincidence: dict):
    """Возвращает меню выбора"""
    length = len(coincidence)
    roster = list(coincidence.values())
    limit = 6
    keyboards = []

    if length <= limit:
        keyboard = Keyboard(inline=True)
        for i in range(length):
            keyboard.add(Callback(f"{roster[i]}", {"name": f"{roster[i]}"}))
            if (i + 1) % 2 == 0:
                keyboard.row()
        if length % 2 != 0:
            keyboard.row()
        keyboards.append(keyboard)

    # Слишком сложная фигня, я написал как чувствую, сори если можно легче
    else:
        count = int(length / limit)
        modul = length % limit
        for i in range(count + 1):
            keyboard = Keyboard(inline=True)
            for j in range(limit):
                if i == count and modul != 0 and j == modul:
                    break
                keyboard.add(Callback(f"{roster[j + i * limit]}", {"name": f"{j + i * limit}"}))
                if (j + 1) % 2 == 0:
                    keyboard.row()
            if modul % 2 != 0 and i == count:
                keyboard.row()
            if i == 0:
                keyboard.add(Callback("Следующая ➡️", {"search_menu": "following"}))
            elif i == count:
                keyboard.add(Callback("⬅️ Предыдущая", {"search_menu": "previous"}))
            else:
                keyboard.add(Callback("⬅️ Предыдущая", {"search_menu": "previous"}))
                keyboard.add(Callback("Следующая ➡️", {"search_menu": "following"}))
            keyboard.row()
            keyboards.append(keyboard)

    return keyboards


async def send_search_menu(message: Message, keyboards):
    keyboard = keyboards[0].add(Callback("Вернутся к выбору", {"initial_menu": "to_selection"})).get_json()
    message_from_bot = await message.answer(message="Были найдены следующие совпадения:", keyboard=keyboard)
    user_db.update_user_message_id(message_from_bot)


@bot.on.private_message(text=["Начать", "/start", "Привет"])
async def handle_start(message: Message):
    """Обработчик начальных сообщений"""
    keyboard, text = await initial_menu_keyboard(message.peer_id)
    message_from_bot = await message.answer(message=text, keyboard=keyboard)
    # Обновляем id последнего сообщения у пользователя
    user_db.update_user_message_id(message_from_bot)


@bot.on.private_message()
async def handle_any_message(message: Message):
    """Обработчик всех сообщений"""
    coincidence = await find_coincidence_group_teacher(message.text, sch)
    is_teacher = user_db.get_is_teacher(message.peer_id)
    message_id = user_db.get_last_message_id(message.peer_id)

    if is_teacher is not None:
        # Удаляем последнее сообщение
        await bot.api.messages.delete(peer_id=message.peer_id, message_ids=message_id, delete_for_all=True)
        # Если пользователь нажал на кнопку Студент
        if is_teacher == 0 and len(coincidence[0]) != 0:
            await send_search_menu(message, search_menu_keyboard(coincidence[0]))

        # Если пользователь нажал на кнопку Преподаватель
        elif is_teacher == 1 and len(coincidence[1]) != 0:
            await send_search_menu(message, search_menu_keyboard(coincidence[1]))

        else:
            text = "Ничего не найдено 😕\n Попробуйте ввести" + (
                " ФИО преподавателя " if is_teacher == 1 else " название группы ") + "ещё раз."
            keyboard = ((Keyboard(inline=True)
                         .add(Callback("Вернутся к выбору", {"initial_menu": "to_selection"})))
                        .get_json())
            message_from_bot = await message.answer(message=text, keyboard=keyboard)
            user_db.update_user_message_id(message_from_bot)


@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=MessageEvent)
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

    if callback == "search_menu":
        if event.payload[callback] == "following":
            pass
        if event.payload[callback] == "previous":
            pass

    # Кнопки начального меню
    if callback == "initial_menu":
        # Клавиатура с кнопкой возврата
        to_selection = Callback("Вернутся к выбору", {"initial_menu": "to_selection"})
        keyboard = Keyboard(inline=True).add(to_selection).get_json()

        # Если нажата кнопка "Преподаватель"
        if event.payload[callback] == "teacher":
            await bot.api.messages.edit(peer_id=peer_id, message_id=message_id,
                                        message="Введите ФИО преподавателя:",
                                        keyboard=keyboard)
            user_db.update_user_is_teacher(peer_id, 1)

        # Если нажата кнопка "Студент"
        if event.payload[callback] == "student":
            await bot.api.messages.edit(peer_id=peer_id, message_id=message_id,
                                        message="Введите название группы:",
                                        keyboard=keyboard)
            user_db.update_user_is_teacher(peer_id, 0)

        # Если нажата кнопка "Вернутся к выбору"
        if event.payload[callback] == "to_selection":
            keyboard, text = await initial_menu_keyboard(peer_id)
            await bot.api.messages.edit(peer_id=peer_id, message_id=message_id, message=text,
                                        keyboard=keyboard)
            user_db.update_user_is_teacher(peer_id, "NULL")


if __name__ == "__main__":
    bot.run_forever()
