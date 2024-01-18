from vkbottle import Bot
from config import bot_token
from handlers import labelers

bot = Bot(bot_token)

for labeler in labelers:
    bot.labeler.load(labeler)

if __name__ == "__main__":
    bot.run_forever()
