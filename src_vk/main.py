from vkbottle import Bot, load_blueprints_from_package
from config import bot_token

bot = Bot(bot_token)

for dp in load_blueprints_from_package("handlers"):
    dp.load(bot)

if __name__ == "__main__":
    bot.run_forever()
