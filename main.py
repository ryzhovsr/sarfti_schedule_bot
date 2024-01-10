import locale
import threading
import traceback
import warnings
import configparser
import telebot
import time
import os
import glob
import requests
import pandas as pd
import contextlib
import ast
from tables import NaturalNameWarning
from datetime import datetime, timedelta
from telebot import types
from bs4 import BeautifulSoup
from io import StringIO
from schedule_data import ScheduleData

# Выключаем предупреждение от библиотеки NaturalNameWarning
warnings.filterwarnings('ignore', category=NaturalNameWarning)
locale.setlocale(locale.LC_ALL, '')

html_website_data = ''  # Страница c исходным html кодом
html_website_soup = ''  # Разобранная html страница

schedule_classes_weekdays = {}  # Расписание учебных занятий в будни (понедельник – пятница)
schedule_classes_saturday = {}  # Расписание учебных занятий в субботу

# Переменные для путей к файлам
user_dir = ''
schedule_current_week_dir = ''

# Смотрим под чем исполняется скрипт, и указываем правильные пути
if os.name == 'nt':
    user_dir = os.path.join(os.getcwd(), 'data\\users\\')
    schedule_current_week_dir = os.path.join(os.getcwd(), 'Data\\schedule_current_week.h5')
else:
    user_dir = os.path.join(os.getcwd(), 'data/users/')
    schedule_current_week_dir = os.path.join(os.getcwd(), 'Data/schedule_current_week.h5')

#######

timing = time.time()  # Инициализируем таймер
key_list_0 = ''
log_dt = ''
menu_1 = {}           # Переменная для хранения главного меню
key_list_groups = {}  # Переменная для хранения списка групп
user_config = {}      # Переменная для хранения данных конфига пользователя

config = configparser.ConfigParser()                # Создаем переменную-парсер нашего конфиг файла
config.read('bot.ini', encoding="utf-8")   # Читаем конфиг
bot_token = str(config['set']['bot_token'])         # Берём токен для работы bot.api
bot = telebot.TeleBot(bot_token, threaded=False)    # Создаем/регистрируем бота
admin_list_id = [int(x) for x in config.get('set', 'admin_list').split(',')]  # Список id админов


# Описываются реакции бота на действия пользователя
def main():
    schedule = ScheduleData()


    # Получаем данные из сайта СарФТИ
    get_data_from_sarfti_website()
    pass

    # если бот получил команды /reset или /start
    @bot.message_handler(commands=['reset', 'start'])
    def any_msg(message):
        log_check(t_user_id=message.from_user.id)
        global menu_1

        print(log_dt + ': user (' + str(message.from_user.id) + ') access start or reset')

        # удалим из чата предыдущий элемент
        remove_message(t_user_id=message.from_user.id, t_message_id=message.message_id)

        # покажем пользователю меню бота
        user_info_read(t_user_id=message.from_user.id)
        send_main_menu(t_user_id=message.from_user.id, t_chat_id=message.chat.id, t_message_id=message.message_id)

    # если бот получил команду от кнопок (callback)
    @bot.callback_query_handler(func=lambda call: True)
    def callback_worker(call):
        global menu_1, key_list_groups, user_config
        log_check(t_user_id=call.message.chat.id)
        print(log_dt + ': user (' + str(call.from_user.id) + ') access ' + str(call.data))

        # если в меню_1 нажата кнопка
        if 'pressed_0_' in call.data and os.path.isfile(user_dir + str(call.from_user.id) + '/step'):

            # если нажата кнопка выбора группы
            if call.data == 'pressed_0_1':
                with contextlib.suppress(Exception):
                    os.remove(user_dir + str(call.from_user.id) + '/step')

                f = open(user_dir + str(call.from_user.id) + '/step_1_1', "w+")
                f.write(str(1))
                f.close()

                key_list_groups = [None] * groups.__len__()
                i = 1
                for key_i in groups:
                    key_list_groups[i - 1] = types.InlineKeyboardButton(text=groups[key_i],
                                                                        callback_data='pressed_1_' + str(i))
                    i = i + 1
                keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=3)
                i = 0
                for key_i in range(0, key_list_groups.__len__()):
                    if key_list_groups.__len__() - i >= 3:
                        keyboard.add(key_list_groups[i], key_list_groups[i + 1], key_list_groups[i + 2])
                        i = i + 3
                        continue
                    if key_list_groups.__len__() - i == 2:
                        keyboard.add(key_list_groups[i], key_list_groups[i + 1])
                        break
                    if key_list_groups.__len__() - i == 1:
                        keyboard.add(key_list_groups[i])
                        break

                key_back = types.InlineKeyboardButton(text='↩ Вернуться в меню', callback_data='pressed_menu')
                keyboard.add(key_back)

                text_out = 'Выберите группу:'
                try:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=text_out,
                                          reply_markup=keyboard)
                except Exception as exc:
                    print(exc)
                    bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                     reply_markup=keyboard)

            # если нажата кнопка расписания
            if call.data == 'pressed_0_2':
                group = ''
                user_info_read(t_user_id=call.message.chat.id)
                for group in groups:
                    if group == str(user_config['group_id']):
                        group = groups[group]
                        break

                if group == '':
                    text_out = 'Выберите группу'
                else:
                    text_out = ('*📅 ' + pd.to_datetime(dates[current_week_id]).strftime('%d %B') + ' - ' +
                                (pd.to_datetime(dates[current_week_id]) + timedelta(days=7)).strftime('%d %B %Yг') +
                                '*\n')

                    day_f = False
                    day_prev = ''

                    for index, row in pd.read_hdf(schedule_current_week_dir,
                                                  current_week_id).query('Группа == @group').iterrows():
                        day_t = str(row['День'])
                        if day_prev == day_t and not day_f:
                            day_f = True
                        if day_prev != day_t:
                            day_prev = day_t
                            day_f = False
                            text_out = text_out + '\n'

                        if day_t == 'ПН' and not day_f:
                            text_out = text_out + '🔹 *ПОНЕДЕЛЬНИК:*\n'
                        if day_t == 'ВТ' and not day_f:
                            text_out = text_out + '🔹 *ВТОРНИК:*\n'
                        if day_t == 'СР' and not day_f:
                            text_out = text_out + '🔹 *СРЕДА:*\n'
                        if day_t == 'ЧТ' and not day_f:
                            text_out = text_out + '🔹 *ЧЕТВЕРГ:*\n'
                        if day_t == 'ПТ' and not day_f:
                            text_out = text_out + '🔹 *ПЯТНИЦА:*\n'
                        if day_t == 'СУБ' and not day_f:
                            text_out = text_out + '🔹 *СУББОТА:*\n'
                        if day_t == 'ВС' and not day_f:
                            text_out = text_out + '🔹 *ВОСКРЕСЕНЬЕ:*\n'

                        t_num = str(row['Пара'])
                        if str(row['Пара']) == '1':
                            t_num = u'\u0031\ufe0f\u20e3'
                        if str(row['Пара']) == '2':
                            t_num = u'\u0032\ufe0f\u20e3'
                        if str(row['Пара']) == '3':
                            t_num = u'\u0033\ufe0f\u20e3'
                        if str(row['Пара']) == '4':
                            t_num = u'\u0034\ufe0f\u20e3'
                        if str(row['Пара']) == '5':
                            t_num = u'\u0035\ufe0f\u20e3'
                        if str(row['Пара']) == '6':
                            t_num = u'\u0036\ufe0f\u20e3'
                        if str(row['Пара']) == '7':
                            t_num = u'\u0037\ufe0f\u20e3'
                        if str(row['Пара']) == '8':
                            t_num = u'\u0038\ufe0f\u20e3'
                        if str(row['Пара']) == '9':
                            t_num = u'\u0039\ufe0f\u20e3'

                        ttype = str(row['Тип']) + ','
                        if str(row['Тип']) == 'Лекция':
                            ttype = u'💬'
                        if str(row['Тип']) == 'Практика':
                            ttype = u'🔥'
                        if 'Лаб' in str(row['Тип']):
                            ttype = (str(row['Тип']).replace('Лаб раб', u'🔥').
                                     replace('Лаб', u'🔥').
                                     replace('1 пг', u'🅰').replace('2 пг', u'🅱'))

                        t_place = str(row['Аудитория'])
                        if 'ОНЛАЙН' in str(row['Аудитория']):
                            t_place = str(row['Аудитория']).replace('ОНЛАЙН', u' 📡')
                        if 'Онлайн 1ДО' in str(row['Аудитория']):
                            t_place = str(row['Аудитория']).replace('Онлайн 1ДО', u'1ДО 📡')
                        if 'Онлайн 2ДО' in str(row['Аудитория']):
                            t_place = str(row['Аудитория']).replace('Онлайн 1ДО', u'2ДО 📡')

                        text_out = (text_out + t_num + ' ' + ttype + ' ' + '[' + t_place + '] ' +
                                    str(row['Предмет']) + ', ' +
                                    str(row['Преподаватель']) + '\n')

                keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=2)
                key_back = types.InlineKeyboardButton(text='↩ Вернуться в меню', callback_data='pressed_menu')
                key_time = types.InlineKeyboardButton(text='🕘 Пары', callback_data='pressed_time')
                key_info = types.InlineKeyboardButton(text='❓ Информация', callback_data='pressed_info')
                keyboard.add(key_time, key_info, key_back)

                try:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=text_out,
                                          reply_markup=keyboard, parse_mode='Markdown')
                except Exception as exc:
                    print(exc)
                    bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                     reply_markup=keyboard, parse_mode='Markdown')

            # если нажата кнопка уведомления
            if call.data == 'pressed_0_3':
                with contextlib.suppress(Exception):
                    with open(user_dir + str(call.message.chat.id) + '/config', "r") as data:
                        user_config = ast.literal_eval(data.read())
                        data.close()

                # запись значения group_id в конфиг пользователя
                if user_config['warning_on_rasp_change'] == 0:
                    user_config['warning_on_rasp_change'] = 1
                else:
                    user_config['warning_on_rasp_change'] = 0

                f = open(user_dir + str(call.message.chat.id) + '/config', "w+")
                f.write("{'group_id':" + str(user_config['group_id']) + ", 'warning_on_rasp_change':" + str(
                    user_config['warning_on_rasp_change']) + ", 'c':" + str(user_config['c']) + ", 'd':" + str(
                    user_config['d']) + "}")
                f.close()

                user_info_read(t_user_id=call.message.chat.id)

                # покажем пользователю основное меню бота
                send_main_menu(t_user_id=call.message.chat.id, t_chat_id=call.message.chat.id,
                               t_message_id=call.message.message_id)

        # если меню_2 нажата кнопка группы
        if 'pressed_1_' in call.data and os.path.isfile(user_dir + str(call.from_user.id) + '/step_1_1'):

            for x in range(1, key_list_groups.__len__() + 1):
                if call.data == 'pressed_1_' + str(x):
                    with contextlib.suppress(Exception):
                        os.remove(user_dir + str(call.message.chat.id) + '/step_1_1')

                    # создадим метку, что пользователь в основном меню бота
                    f = open(user_dir + str(call.message.chat.id) + '/step', "w+")
                    f.write('1')
                    f.close()

                    with contextlib.suppress(Exception):
                        with open(user_dir + str(call.message.chat.id) + '/config', "r") as data:
                            user_config = ast.literal_eval(data.read())
                            data.close()

                    # запись значения group_id в конфиг пользователя
                    user_config['group_id'] = list(groups.keys())[x - 1]
                    f = open(user_dir + str(call.message.chat.id) + '/config', "w+")
                    f.write("{'group_id':" + str(user_config['group_id']) + ", 'warning_on_rasp_change':" + str(
                        user_config['warning_on_rasp_change']) + ", 'c':" + str(user_config['c']) + ", 'd':" + str(
                        user_config['d']) + "}")
                    f.close()

                    user_info_read(t_user_id=call.message.chat.id)

                    # покажем пользователю основное меню бота
                    send_main_menu(t_user_id=call.message.chat.id, t_chat_id=call.message.chat.id,
                                   t_message_id=call.message.message_id)

                    break

        # если нажата кнопка возврата в основное меню
        if 'pressed_menu' in call.data:
            with contextlib.suppress(Exception):
                os.remove(user_dir + str(call.message.chat.id) + '/step_1_1')

            # покажем пользователю меню бота
            send_main_menu(t_user_id=call.message.chat.id, t_chat_id=call.message.chat.id,
                           t_message_id=call.message.message_id)

        # если нажата кнопка очистки уведомления
        if 'pressed_del' in call.data:
            with open(user_dir + str(call.message.chat.id) + '/del_msg.id', "r") as del_msg:
                del_msg_id = del_msg.read()
                del_msg.close()

            with contextlib.suppress(Exception):
                bot.delete_message(chat_id=call.message.chat.id, message_id=int(del_msg_id))

            with contextlib.suppress(Exception):
                os.remove(user_dir + str(call.message.chat.id) + '/del_msg.id')

        # если нажата кнопка информации в расписании
        if call.data == 'pressed_info':
            text_out = '❓ Что означают значки в расписании занятий:\n\n' + \
                       u'\u0031\ufe0f\u20e3' + ' - номер пары\n' + \
                       u'💬' + ' - лекция\n' + \
                       u'🔥' + ' - практика, лаб. раб.\n' + \
                       u'📡' + ' - онлайн\n' + \
                       u'🅰' + ' - подгруппа 1\n' + \
                       u'🅱' + ' - подгруппа 2'

            keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=2)
            key_back = types.InlineKeyboardButton(text='↩ Вернуться в меню', callback_data='pressed_menu')
            key_time = types.InlineKeyboardButton(text='🕘 Пары', callback_data='pressed_time')
            key_rasp = types.InlineKeyboardButton(text='📅 Расписание', callback_data='pressed_0_2')
            keyboard.add(key_time, key_rasp, key_back)

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=text_out,
                                      reply_markup=keyboard)
            except Exception as exc:
                print(exc)
                bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                 reply_markup=keyboard)

        # если нажата кнопка пар в расписании
        if call.data == 'pressed_time':
            text_out = '🕘 Расписание пар.\n\n' + \
                       '🔹 *ПОНЕДЕЛЬНИК - ПЯТНИЦА:*\n'
            for item in schedule_classes_weekdays.items():
                if '1' in item[0]:
                    text_out = text_out + u'\u0031\ufe0f\u20e3'
                if '2' in item[0]:
                    text_out = text_out + u'\u0032\ufe0f\u20e3'
                if '3' in item[0]:
                    text_out = text_out + u'\u0033\ufe0f\u20e3'
                if '4' in item[0]:
                    text_out = text_out + u'\u0034\ufe0f\u20e3'
                if '5' in item[0]:
                    text_out = text_out + u'\u0035\ufe0f\u20e3'
                if '6' in item[0]:
                    text_out = text_out + u'\u0036\ufe0f\u20e3'
                if '7' in item[0]:
                    text_out = text_out + u'\u0037\ufe0f\u20e3'
                if '8' in item[0]:
                    text_out = text_out + u'\u0038\ufe0f\u20e3'
                if '9' in item[0]:
                    text_out = text_out + u'\u0039\ufe0f\u20e3'
                text_out = text_out + ' ' + item[1] + '\n'

            text_out = text_out + '\n🔹 *СУББОТА:*\n'
            for item in schedule_classes_saturday.items():
                if '1' in item[0]:
                    text_out = text_out + u'\u0031\ufe0f\u20e3'
                if '2' in item[0]:
                    text_out = text_out + u'\u0032\ufe0f\u20e3'
                if '3' in item[0]:
                    text_out = text_out + u'\u0033\ufe0f\u20e3'
                if '4' in item[0]:
                    text_out = text_out + u'\u0034\ufe0f\u20e3'
                if '5' in item[0]:
                    text_out = text_out + u'\u0035\ufe0f\u20e3'
                if '6' in item[0]:
                    text_out = text_out + u'\u0036\ufe0f\u20e3'
                if '7' in item[0]:
                    text_out = text_out + u'\u0037\ufe0f\u20e3'
                if '8' in item[0]:
                    text_out = text_out + u'\u0038\ufe0f\u20e3'
                if '9' in item[0]:
                    text_out = text_out + u'\u0039\ufe0f\u20e3'
                text_out = text_out + ' ' + item[1] + '\n'

            keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=2)
            key_back = types.InlineKeyboardButton(text='↩ Вернуться в меню', callback_data='pressed_menu')
            key_info = types.InlineKeyboardButton(text='❓ Информация', callback_data='pressed_info')
            key_rasp = types.InlineKeyboardButton(text='📅 Расписание', callback_data='pressed_0_2')
            keyboard.add(key_rasp, key_info, key_back)

            try:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=text_out,
                                      reply_markup=keyboard, parse_mode='Markdown')
            except Exception as exc:
                print(exc)
                bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                 reply_markup=keyboard, parse_mode='Markdown')

    # если пользователь скинул боту что-то, что боту не нужно - удалим это из чата
    @bot.message_handler(content_types=['sticker', 'text', 'location', 'photo', 'document'])
    def any_msg(message):
        log_check(t_user_id=message.from_user.id)

        # удалим из чата предыдущий элемент
        remove_message(t_user_id=message.from_user.id, t_message_id=message.message_id)

    my_thread = threading.Thread(target=timecheck)
    my_thread.start()

    # цикл получения сообщений для бота с проверкой раз в 2 секунды
    while True:
        try:
            bot.polling(non_stop=True)
            time.sleep(2)

        except Exception as e:
            print(e)
            # или import traceback; traceback.print_exc() для печати полной информации
            traceback.print_exc()
            # time.sleep(1)

        time.sleep(1)


def timecheck():
    global timing, current_week_id, bot, groups

    while True:
        if time.time() - timing > 300:
            timing = time.time()
            now_time = datetime.now()
            store_back = pd.read_hdf(schedule_current_week_dir, current_week_id)
            get_data_from_sarfti_website()
            store_now = pd.read_hdf(schedule_current_week_dir, current_week_id)
            df_diff = pd.concat([store_back, store_now]).drop_duplicates(keep=False)

            if (not store_now.equals(store_back)) and (now_time.hour >= 7) and (now_time.hour <= 21):
                for subdir, dirs, files in os.walk(user_dir):
                    for file in files:
                        if 'config' in file:
                            with contextlib.suppress(Exception):
                                user_id = subdir.replace(user_dir, '')
                                with open(user_dir + str(user_id) + '/config', "r") as udata:
                                    user_conf = ast.literal_eval(udata.read())
                                    udata.close()

                                if user_conf['warning_on_rasp_change'] == 1:
                                    for dif_group in df_diff['Группа']:
                                        if dif_group == groups[str(user_conf['group_id'])]:

                                            text_out2 = '*⚠ Произошли изменения в расписании! ⚠*'

                                            keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=1)
                                            key_del = types.InlineKeyboardButton(text='♻ Закрыть уведомление ♻',
                                                                                 callback_data='pressed_del')
                                            keyboard.add(key_del)

                                            with contextlib.suppress(Exception):
                                                bot_msg = bot.send_message(chat_id=int(user_id), text=text_out2,
                                                                           reply_markup=keyboard, parse_mode='Markdown')

                                                with contextlib.suppress(Exception):
                                                    os.remove(user_dir + user_id + '/del_msg.id')

                                                del_msg_u = open(user_dir + user_id + '/del_msg.id', "w+")
                                                del_msg_u.write(str(bot_msg.message_id))
                                                del_msg_u.close()

                                            break

                            time.sleep(60)

        time.sleep(5)


# Функция для заполнения/обновления данных со страницы сайта СарФТИ. Вызывается периодический
def get_data_from_sarfti_website():
    global html_website_data, html_website_soup, schedule_classes_weekdays, schedule_classes_saturday, groups, \
        teachers, dates, places, current_week_id, schedule_current_week

    with contextlib.suppress(Exception):
        # Методом HTTP.POST забираем нужную страницу с сайта
        html_website_data = requests.post('https://sarfti.ru/?page_id=20',
                                          data={'page_id': '20', 'view': 'Просмотр'}).text
        # Разбираем страницу
        html_website_soup = BeautifulSoup(html_website_data, 'lxml')

        # Получаем сырые данные групп, преподавателей, мест (аудиторий) и дат
        groups_raw_data = [i.findAll('option') for i in
                           html_website_soup.findAll('select', attrs={'name': 'group_id'})]
        teachers_raw_data = [i.findAll('option') for i in
                             html_website_soup.findAll('select', attrs={'name': 'teacher_id'})]
        places_raw_data = [i.findAll('option') for i in
                           html_website_soup.findAll('select', attrs={'name': 'place_id'})]
        dates_raw_data = [i.findAll('option') for i in
                          html_website_soup.findAll('select', attrs={'name': 'date_id'})]

        # Получаем раписание занятий на будние дни
        for item in html_website_soup.findAll('table', attrs={'style': 'width: 274px; border-style: none;'}):
            schedule_classes_weekdays = dict(x.split('=') for x in item.text.
                                             replace('\n\n\n1 пара', '1 пара').
                                             replace('\xa0', ' ').
                                             replace('\n\n\n', ';').
                                             replace('\n–\n', '=').
                                             replace('\n', ' | ')[:-1].split(';'))
            break

        # Получаем раписание занятий на субботу
        for item in html_website_soup.findAll('table', attrs={'style': 'width: 273px; border: none;'}):
            schedule_classes_weekdays = dict(x.split('=') for x in item.text.
                                             replace('\n\n\n1 пара', '1 пара').
                                             replace('\xa0', ' ').
                                             replace('\n\n\n', ';').
                                             replace('\n–\n', '=').
                                             replace('\n', ' | ')[:-1].split(';'))
            break

        # Прогоняем цикл по всем сырым данным групп, преподавателей, мест (аудиторий) и дат
        for item in [groups_raw_data, teachers_raw_data, places_raw_data, dates_raw_data]:
            for i in range(0, item[0].__len__()):
                # Если элемент не содержит "Выберите", то загоняем его в соответствующий список
                if 'Выберите' not in item[0][i].text:
                    if item == groups_raw_data:
                        groups[item[0][i].attrs['value']] = item[0][i].text
                    if item == teachers_raw_data:
                        teachers[item[0][i].attrs['value']] = item[0][i].text
                    if item == places_raw_data:
                        places[item[0][i].attrs['value']] = item[0][i].text
                    if item == dates_raw_data:
                        dates[item[0][i].attrs['value']] = item[0][i].text

        # Удаляем переменные, хранящие необработанные данные из памяти, т.к. мы их обработали
        del groups_raw_data, teachers_raw_data, places_raw_data, dates_raw_data

        # Определяем id текущей (рабочей) недели
        time_now = datetime.now()
        for week_id in list(dates):
            if (pd.to_datetime(dates[week_id]) - timedelta(days=1) <= time_now <
                    pd.to_datetime(dates[week_id]) + timedelta(days=7)):
                # current_week = pd.to_datetime(in_dates[week_id]).strftime('%Y-%m-%d')
                current_week_id = week_id
                break

        # Данные сайта по управлению расписанием
        schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                 data={'login': '', 'password': '', 'guest': 'Войти+как+Гость'})

        # Данные сайта по печати (вывода) расписания на текущую неделю
        current_week_schedule_html = requests.post('http://scs.sarfti.ru/date/printT',
                                                   data={'id': current_week_id, 'show': 'Распечатать',
                                                         'list': 'list', 'compact': 'compact'},
                                                   cookies=schedule_management_html.history[0].cookies)

        current_week_schedule_html.encoding = 'utf-8'

        for item in pd.read_html(StringIO(current_week_schedule_html.text)):
            if 'День' and 'Пара' in item:
                with contextlib.suppress(Exception):
                    os.remove(schedule_current_week_dir)

                file = pd.HDFStore(schedule_current_week_dir)
                file[current_week_id] = item
                file.close()
                schedule_current_week = item

                break


# функция показа основного меню
def send_main_menu(t_user_id, t_chat_id, t_message_id):
    global menu_1, key_list_0, user_config

    # если есть какие-то "метки" для навигации по меню бота - удаляем, так как вызван режим "всё сначала"
    file_list = glob.glob(user_dir + str(t_user_id) + '/step*')
    for filePath in file_list:
        try:
            os.remove(filePath)
        except Exception as e:
            print(e)
            print(log_dt + ": Error while deleting file : ", filePath)

    # создадим метку, что пользователь в корневом меню бота
    f = open(user_dir + str(t_user_id) + '/step', "w+")
    f.write('1')
    f.close()

    menu_1 = {1: '👥 Выбрать группу', 2: '📅 Расписание', 3: '🔕 Уведомление [выкл]'}

    user_info_read(t_user_id)

    if user_config['group_id'] is not None:
        try:
            menu_1[1] = '👥 ' + groups[str(user_config['group_id'])]
        except Exception as e:
            print(e)
            menu_1[1] = '👥 Выбрать группу'
    else:
        menu_1[1] = '👥 Выбрать группу'

    if user_config['warning_on_rasp_change'] == (0 | 1) and user_config['warning_on_rasp_change'] is not None:
        if user_config['warning_on_rasp_change'] == 0:
            menu_1[3] = '🔕 Уведомление [выкл]'
        if user_config['warning_on_rasp_change'] == 1:
            menu_1[3] = '🔔 Уведомление [вкл]'
    else:
        menu_1[3] = '🔕 Уведомление [выкл]'
    key_list_0 = {}
    for i in range(1, menu_1.__len__() + 1):
        vars()['key_0_' + str(i)] = types.InlineKeyboardButton(
            text=str(menu_1[i]),
            callback_data='pressed_0_' + str(i))
        key_list_0[i] = eval('key_0_' + str(i))

    keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=1)
    for key_i in range(1, key_list_0.__len__() + 1):
        keyboard.add(key_list_0[key_i])

    text_out = 'Привет!'
    try:
        bot.edit_message_text(chat_id=t_chat_id, message_id=t_message_id,
                              text=text_out,
                              reply_markup=keyboard)
    except Exception:
        bot.send_message(chat_id=t_chat_id,
                         text=text_out, reply_markup=keyboard)


# функция чтения конфига пользователя
def user_info_read(t_user_id):
    global user_config
    if os.path.exists(user_dir + str(t_user_id) + '/config'):
        try:
            with open(user_dir + str(t_user_id) + '/config', "r") as data:
                user_config = ast.literal_eval(data.read())
                data.close()
        except Exception as exc:
            print(exc)
            os.remove(user_dir + str(t_user_id) + '/config')
            f = open(user_dir + str(t_user_id) + '/config', "w+")
            f.write("{'group_id':'', 'warning_on_rasp_change':0, 'c':0, 'd':0}")
            f.close()
            with open(user_dir + str(t_user_id) + '/config', "r") as data:
                user_config = ast.literal_eval(data.read())
                data.close()
    else:
        f = open(user_dir + str(t_user_id) + '/config', "w+")
        f.write("{'group_id':'', 'warning_on_rasp_change':0, 'c':0, 'd':0}")
        f.close()
        with open(user_dir + str(t_user_id) + '/config', "r") as data:
            user_config = ast.literal_eval(data.read())
            data.close()


def time_check():
    global timing, current_week_id, bot, groups

    while True:
        if time.time() - timing > 300:
            timing = time.time()
            now_time = datetime.now()
            store_back = pd.read_hdf(schedule_current_week_dir, current_week_id)
            get_data_from_sarfti_website()
            store_now = pd.read_hdf(schedule_current_week_dir, current_week_id)
            df_diff = pd.concat([store_back, store_now]).drop_duplicates(keep=False)

            if (not store_now.equals(store_back)) and (now_time.hour >= 7) and (now_time.hour <= 21):
                for subdir, dirs, files in os.walk(user_dir):
                    for file in files:
                        if 'config' in file:
                            with contextlib.suppress(Exception):
                                user_id = subdir.replace(user_dir, '')
                                with open(user_dir + str(user_id) + '/config', "r") as udata:
                                    user_conf = ast.literal_eval(udata.read())
                                    udata.close()

                                if user_conf['warning_on_rasp_change'] == 1:
                                    for dif_group in df_diff['Группа']:
                                        if dif_group == groups[str(user_conf['group_id'])]:

                                            text_out2 = '*⚠ Произошли изменения в расписании! ⚠*'

                                            keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=1)
                                            key_del = types.InlineKeyboardButton(text='♻ Закрыть уведомление ♻',
                                                                                 callback_data='pressed_del')
                                            keyboard.add(key_del)

                                            with contextlib.suppress(Exception):
                                                bot_msg = bot.send_message(chat_id=int(user_id), text=text_out2,
                                                                           reply_markup=keyboard, parse_mode='Markdown')

                                                with contextlib.suppress(Exception):
                                                    os.remove(user_dir + user_id + '/del_msg.id')

                                                del_msg_u = open(user_dir + user_id + '/del_msg.id', "w+")
                                                del_msg_u.write(str(bot_msg.message_id))
                                                del_msg_u.close()

                                            break

                            time.sleep(60)

        time.sleep(5)


# функция логирования и проверки каталога пользователя
def log_check(t_user_id):
    global log_dt
    # берем время/дату для лога
    log_dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # если нет каталога для подкаталогов пользователей, то создадим его
    if not os.path.isdir(user_dir):
        os.mkdir(user_dir)

    # если нет каталога пользователя, то создадим его
    if not os.path.isdir(user_dir + str(t_user_id)):
        os.mkdir(user_dir + str(t_user_id))


# Функция удаления элементов из чата
def remove_message(t_user_id, t_message_id):
    print(log_dt + ': reg user (' + str(t_user_id) + ') remove message from chat')
    try:
        bot.delete_message(chat_id=t_user_id, message_id=t_message_id)
    except Exception as exc:
        print(exc)
        print(log_dt + ': reg user (' + str(t_user_id) + ') error remove message from chat')


# Точка входа
if __name__ == '__main__':
    main()
