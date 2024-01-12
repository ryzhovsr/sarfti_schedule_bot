from vkbottle import Keyboard, Callback, GroupEventType
from vkbottle.bot import Bot, Message, MessageEvent

from schedule_data import ScheduleData
from vk_userdb import UserDatabase

token = "vk1.a.j8Yt1zZf7KLV75zluh9yXUmfoqE_lbgWZzX9xZaHgvm6kO8C96_ah-l7NXqBakFgzimC8AuMw0Fq0M4KbGQFUjzLrT3DtsFW8yHtdTSWbZY9JP2OhF12OVUwLVN_7ddkj7yxQdNFh-pgatYgWLzSvcA-2SrnG04jvADcNMmg-eUSEXW3j9kEmu3unAwnx2JcrqnY0DgpV1bmyzWEIFRoLA"
bot = Bot(token)
sch = ScheduleData()
user_db = UserDatabase()


async def send_initial_menu(peer_id):
    """Возвращает начальное меню"""
    user = await bot.api.users.get(peer_id)

    keyboard = (
        Keyboard(inline=True)
        .add(Callback("Преподавателя", {"initial_menu": "teacher"}))
        .add(Callback("Студента", {"initial_menu": "student"}))
        .row()
        .add(Callback("Инфо", {"info": "info"}))
    ).get_json()

    text = f'Привет, {user[0].first_name} {user[0].last_name}!👋\n Какое расписание хочешь получить?'

    return keyboard, text


@bot.on.private_message(text=["Начать", "/start", "Привет"])
async def handle_start(message: Message):
    """Обработчик команды /start"""
    keyboard, text = await send_initial_menu(message.peer_id)
    message_from_bot = await message.answer(message=text, keyboard=keyboard)
    # Обновляем id последнего сообщения у пользователя
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

    # Кнопки начального меню
    if callback == "initial_menu":
        # Клавиатура с кнопкой возврата
        to_selection = Callback("Вернутся к выбору", {"initial_menu": "to_selection"})
        keyboard = Keyboard(inline=True).add(to_selection).get_json()

        # Если нажата кнопка "Преподаватель"
        if event.payload[callback] == "teacher":
            await bot.api.messages.edit(peer_id=peer_id, message_id=message_id, message="Введите ФИО преподавателя:",
                                        keyboard=keyboard)

        # Если нажата кнопка "Студент"
        if event.payload[callback] == "student":
            await bot.api.messages.edit(peer_id=peer_id, message_id=message_id, message="Введите название группы:",
                                        keyboard=keyboard)

        # Если нажата кнопка "Вернутся к выбору"
        if event.payload[callback] == "to_selection":
            keyboard, text = await send_initial_menu(peer_id)
            await bot.api.messages.edit(peer_id=peer_id, message_id=message_id, message=text,
                                        keyboard=keyboard)


if __name__ == "__main__":
    bot.run_forever()
