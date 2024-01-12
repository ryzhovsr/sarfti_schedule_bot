from vkbottle import Keyboard, Text, Callback
from vkbottle.bot import Bot, Message
from vkbottle_types import GroupTypes
from vkbottle_types.events import GroupEventType

from schedule_data import ScheduleData
from utils import find_coincidence_group_teacher

token = "vk1.a.j8Yt1zZf7KLV75zluh9yXUmfoqE_lbgWZzX9xZaHgvm6kO8C96_ah-l7NXqBakFgzimC8AuMw0Fq0M4KbGQFUjzLrT3DtsFW8yHtdTSWbZY9JP2OhF12OVUwLVN_7ddkj7yxQdNFh-pgatYgWLzSvcA-2SrnG04jvADcNMmg-eUSEXW3j9kEmu3unAwnx2JcrqnY0DgpV1bmyzWEIFRoLA"
bot = Bot(token)
sch = ScheduleData()


# Пернести в другой модуль
def get_groups_teachers_fab(groups_and_teachers_data):
    """Возвращает клавиатуру с группами и ФИО преподавателей"""
    builder = Keyboard(inline=True)
    count = 0  # Счетчик кнопок

    for dic in groups_and_teachers_data:
        for item, value in dic.items():
            builder.add(
                Callback(f"{value}", {"callback": f"{item}"})
            )

    return builder.get_json()


@bot.on.private_message(text=["Начать", "/start", "Привет"])
async def handle_start(message: Message):
    """Обработчик команды /start"""
    user = await bot.api.users.get(message.from_id)

    keyboard = (
        Keyboard(inline=True)
        .add(Callback("Преподавателя", {"callback": "teacher"}))
        .add(Callback("Студента", {"callback": "student"}))
    ).get_json()

    message_from_bot = await message.answer(message=f'Привет, {user[0].first_name} {user[0].last_name}!👋\n'
                                 f'Какое расписание хочешь получить?',
                         keyboard=keyboard)

    # await bot.api.messages.delete(peer_id=message.peer_id, message_ids=message.id + 1, delete_for_all=True) удаление сообщение у бота


@bot.on.private_message()
async def handle_any_message(message: Message):
    """Обработчик всех сообщений"""

    # Находим совпадения между сообщением пользователя и группами/преподавателями
    coincidence = await find_coincidence_group_teacher(message.text, sch)

    # Если совпадения не пустые
    if coincidence[0] or coincidence[1]:
        pass
        await message.answer(message="Были найдены следующие совпадения:",
                             keyboard=get_groups_teachers_fab(coincidence))
    else:
        await message.answer("Ничего не найдено😕\n Попробуйте ввести название группы / ФИО преподавателя ещё раз.")

#Отлов callback
@bot.on.raw_event(GroupEventType.MESSAGE_EVENT, dataclass=GroupTypes.MessageEvent)
async def message_event_handler(event: GroupTypes.MessageEvent):
    if event.object.payload["callback"] == "teacher":
        await bot.api.messages.delete(peer_id=event.peer_id, message_ids=event.object.


if __name__ == "__main__":
    bot.run_forever()
