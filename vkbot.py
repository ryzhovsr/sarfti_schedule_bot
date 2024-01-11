from vkbottle.bot import Bot, Message

token = "vk1.a.j8Yt1zZf7KLV75zluh9yXUmfoqE_lbgWZzX9xZaHgvm6kO8C96_ah-l7NXqBakFgzimC8AuMw0Fq0M4KbGQFUjzLrT3DtsFW8yHtdTSWbZY9JP2OhF12OVUwLVN_7ddkj7yxQdNFh-pgatYgWLzSvcA-2SrnG04jvADcNMmg-eUSEXW3j9kEmu3unAwnx2JcrqnY0DgpV1bmyzWEIFRoLA"
bot = Bot(token)


@bot.on.private_message(text=["Начать", "/start", "Привет"])
async def handle_start(message: Message):
    """Обработчик команды /start"""
    user = await bot.api.users.get(message.from_id)
    await message.answer(f'Привет, {user[0].first_name} {user[0].last_name}!👋\n'
                         f'Введите название группы / ФИО преподавателя.')
    #await bot.api.messages.delete(peer_id=message.peer_id, message_ids=message.id + 1, delete_for_all=True) удаление сообщение у бота

if __name__ == "__main__":
    bot.run_forever()