# -*- coding: utf-8 -*-

# подключаем различные библиотеки
import ast
import configparser
import datetime
import glob
import locale
import os
import pandas as pd
import requests
import telebot
import time
import threading
import traceback
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date
from telebot import types
from io import StringIO
import tables
# pytelegrambotapi requests pandas lxml bs4 urllib3 html_table_parser pytables

locale.setlocale(locale.LC_ALL, '')

# объявляем переменные
in_groups = {} # список групп и их group_id
in_teachers = {} # список преподов и их teacher_id
in_places = {} # список аудиторий и их place_id
in_dates = {} # список учебных недель и их date_id
in_week = {} # таблица с расписанием текущей недели
week_id = '' # id текущей недели
# все списки выше необходимы для работы бота в режиме "выбор группы/препода/недели/аудитории"
soup = '' # разобранная страница
raw_input = '' # неразобранная страница
# обе переменных нужны для отладки приложения, так все первичные данные
v_version = '22.07.22' # версия скрипта
c_token = '' #
config = configparser.ConfigParser() # создаем переменную-парсер нашего конфиг файла
config.read('bot.ini', encoding="utf-8") # читаем конфиг
bot_token = str(config['set']['token']) # берём токен для работы bot.api
#c_admin_list = [int(x) for x in config.get('set', 'admin_list').split(',')]
bot = telebot.TeleBot(bot_token, threaded=False) # создаем/регистрируем бота
userdir = '' # переменная для пути к каталогу пользователей
menu_1 = {} # переменная для хранения главного меню
key_list_groups = {} # переменная для хранения списка групп
user_config = {} # переменная для хранения данных конфига пользователя

# здесь хитрость: смотрим, под чем исполняется скрипт, и указываем правильные пути
if os.name == 'nt':
    userdir = os.path.join(os.getcwd(), 'users\\')
else:
    userdir = os.path.join(os.getcwd(), 'users/')

# инициализируем таймер
timing = time.time()

# описываем функции
# тело скрипта
def main():
    # здесь описываем реакции бота на действия пользователя

    # заполняем списки (вызывать переодически, по событию или таймеру)
    loadin()
    pass

    # если бот получил команды /reset или /start
    @bot.message_handler(commands=['reset', 'start'])
    def any_msg(message):
        logcheck(t_user_id=message.from_user.id)
        global menu_1

        print(log_dt + ': user (' + str(message.from_user.id) + ') access start or reset')

        # удалим из чата предыдущий элемент
        remove_message(t_user_id = message.from_user.id, t_message_id=message.message_id)

        # покажем пользователю меню бота
        user_info_read(t_user_id = message.from_user.id)
        send_main_menu(t_user_id = message.from_user.id, t_chat_id=message.chat.id, t_message_id=message.message_id)

    # если бот получил команду от кнопок (callback)
    @bot.callback_query_handler(func=lambda call: True)
    def callback_worker(call):
        global menu_1, key_list_groups, user_config
        logcheck(t_user_id = call.message.chat.id)
        print(log_dt + ': user (' + str(call.from_user.id) + ') access ' + str(call.data))

        # если в меню_1 нажата кнопка
        if 'pressed_0_' in call.data and os.path.isfile(userdir + str(call.from_user.id) + '/stepm'):

            # если нажата кнопка выбора группы
            if call.data == 'pressed_0_1':
                try:
                    os.remove(userdir + str(call.from_user.id) + '/stepm')
                except:
                    pass

                f = open(userdir + str(call.from_user.id) + '/step_1_1', "w+")
                f.write(str(1))
                f.close()

                key_list_groups = [None] * in_groups.__len__()
                i = 1
                for key_i in in_groups:
                    key_list_groups[i - 1] = types.InlineKeyboardButton(text=in_groups[key_i], callback_data='pressed_1_' + str(i))
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
                except:
                    bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                     reply_markup=keyboard)

            # если нажата кнопка расписания
            if call.data == 'pressed_0_2':
                group = ''
                user_info_read(t_user_id=call.message.chat.id)
                for group in in_groups:
                    if group == str(user_config['group_id']):
                        group = in_groups[group]
                        break

                if group == '':
                    text_out = 'Выберите группу'
                else:
                    today = datetime.now()
                    text_out = '*📅 ' + pd.to_datetime(in_dates[week_id]).strftime('%d %B') + ' - ' + \
                               (pd.to_datetime(in_dates[week_id]) + timedelta(days=7)).strftime('%d %B %Yг') + '*\n'

                    dayf = False
                    dayprev = ''
                    for index, row in pd.read_hdf('in_week.h5', week_id).query('Группа == @group').iterrows():
                        dayt = str(row['День'])
                        if dayprev == dayt and dayf == False: dayf = True
                        if dayprev != dayt:
                            dayprev = dayt
                            dayf = False
                            text_out = text_out + '\n'

                        if dayt == 'ПН' and dayf == False:
                            text_out = text_out + '🔹 *ПОНЕДЕЛЬНИК:*\n'
                        if dayt == 'ВТ' and dayf == False:
                            text_out = text_out + '🔹 *ВТОРНИК:*\n'
                        if dayt == 'СР' and dayf == False:
                            text_out = text_out + '🔹 *СРЕДА:*\n'
                        if dayt == 'ЧТ' and dayf == False:
                            text_out = text_out + '🔹 *ЧЕТВЕРГ:*\n'
                        if dayt == 'ПТ' and dayf == False:
                            text_out = text_out + '🔹 *ПЯТНИЦА:*\n'
                        if dayt == 'СУБ' and dayf == False:
                            text_out = text_out + '🔹 *СУББОТА:*\n'
                        if dayt == 'ВС' and dayf == False:
                            text_out = text_out + '🔹 *ВОСКРЕСЕНЬЕ:*\n'

                        tnum = str(row['Пара'])
                        if str(row['Пара']) == '1': tnum = u'\u0031\ufe0f\u20e3'
                        if str(row['Пара']) == '2': tnum = u'\u0032\ufe0f\u20e3'
                        if str(row['Пара']) == '3': tnum = u'\u0033\ufe0f\u20e3'
                        if str(row['Пара']) == '4': tnum = u'\u0034\ufe0f\u20e3'
                        if str(row['Пара']) == '5': tnum = u'\u0035\ufe0f\u20e3'
                        if str(row['Пара']) == '6': tnum = u'\u0036\ufe0f\u20e3'
                        if str(row['Пара']) == '7': tnum = u'\u0037\ufe0f\u20e3'
                        if str(row['Пара']) == '8': tnum = u'\u0038\ufe0f\u20e3'
                        if str(row['Пара']) == '9': tnum = u'\u0039\ufe0f\u20e3'

                        ttype = str(row['Тип']) + ','
                        if str(row['Тип']) == 'Лекция': ttype = u'💬'
                        if str(row['Тип']) == 'Практика': ttype = u'🔥'
                        if 'Лаб' in str(row['Тип']): ttype = str(row['Тип']).replace('Лаб раб', u'🔥').replace('Лаб', u'🔥').replace('1 пг', u'🅰').replace('2 пг', u'🅱')

                        tplace = str(row['Аудитория'])
                        if 'ОНЛАЙН' in str(row['Аудитория']): tplace = str(row['Аудитория']).replace('ОНЛАЙН', u' 📡')
                        if 'Онлайн 1ДО' in str(row['Аудитория']): tplace = str(row['Аудитория']).replace('Онлайн 1ДО', u'1ДО 📡')
                        if 'Онлайн 2ДО' in str(row['Аудитория']): tplace = str(row['Аудитория']).replace('Онлайн 1ДО', u'2ДО 📡')

                        text_out = text_out + \
                                   tnum + ' ' + ttype + ' ' + \
                                   '[' + tplace + '] ' + \
                                   str(row['Предмет']) + ', ' + \
                                   str(row['Преподаватель']) + '\n'

                keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=2)
                key_back = types.InlineKeyboardButton(text='↩ Вернуться в меню', callback_data='pressed_menu')
                key_time = types.InlineKeyboardButton(text='🕘 Пары', callback_data='pressed_time')
                key_info = types.InlineKeyboardButton(text='❓ Информация', callback_data='pressed_info')
                keyboard.add(key_time, key_info, key_back)

                try:
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          text=text_out,
                                          reply_markup=keyboard, parse_mode='Markdown')
                except:
                    bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                     reply_markup=keyboard, parse_mode='Markdown')

            # если нажата кнопка уведомления
            if call.data == 'pressed_0_3':
                try:
                    with open(userdir + str(call.message.chat.id) + '/config', "r") as data:
                        user_config = ast.literal_eval(data.read())
                        data.close()
                except:
                    pass
                # запись значения group_id в конфиг пользователя
                if user_config['warning_on_rasp_change'] == 0:
                    user_config['warning_on_rasp_change'] = 1
                else:
                    user_config['warning_on_rasp_change'] = 0

                f = open(userdir + str(call.message.chat.id) + '/config', "w+")
                f.write("{'group_id':" + str(user_config['group_id']) + ", 'warning_on_rasp_change':" + str(
                    user_config['warning_on_rasp_change']) + ", 'c':" + str(user_config['c']) + ", 'd':" + str(
                    user_config['d']) + "}")
                f.close()

                user_info_read(t_user_id=call.message.chat.id)

                # покажем пользователю основное меню бота
                send_main_menu(t_user_id=call.message.chat.id, t_chat_id=call.message.chat.id,
                               t_message_id=call.message.message_id)

        # если меню_2 нажата кнопка группы
        if 'pressed_1_' in call.data and os.path.isfile(userdir + str(call.from_user.id) + '/step_1_1'):

            for x in range(1, key_list_groups.__len__() + 1):
                if call.data == 'pressed_1_' + str(x):
                    try:
                        os.remove(userdir + str(call.message.chat.id) + '/step_1_1')
                    except:
                        pass

                    # создадим метку, что пользователь в основном меню бота
                    f = open(userdir + str(call.message.chat.id) + '/stepm', "w+")
                    f.write('1')
                    f.close()

                    try:
                        with open(userdir + str(call.message.chat.id) + '/config', "r") as data:
                            user_config = ast.literal_eval(data.read())
                            data.close()
                    except:
                        pass
                    # запись значения group_id в конфиг пользователя
                    user_config['group_id'] = list(in_groups.keys())[x - 1]
                    f = open(userdir + str(call.message.chat.id) + '/config', "w+")
                    f.write("{'group_id':" + str(user_config['group_id']) + ", 'warning_on_rasp_change':" + str(user_config['warning_on_rasp_change']) + ", 'c':" + str(user_config['c']) + ", 'd':" + str(user_config['d']) + "}")
                    f.close()

                    user_info_read(t_user_id=call.message.chat.id)

                    # покажем пользователю основное меню бота
                    send_main_menu(t_user_id=call.message.chat.id, t_chat_id=call.message.chat.id,
                                   t_message_id=call.message.message_id)

                    break

        # если нажата кнопка возврата в основное меню
        if 'pressed_menu' in call.data:
            try:
                os.remove(userdir + str(call.message.chat.id) + '/step_1_1')
            except:
                pass

            # покажем пользователю меню бота
            send_main_menu(t_user_id=call.message.chat.id, t_chat_id=call.message.chat.id,
                           t_message_id=call.message.message_id)

        # если нажата кнопка очиски уведомления
        if 'pressed_del' in call.data:
            with open(userdir + str(call.message.chat.id) + '/delmsg.id', "r") as delmsg:
                delmsg_id = delmsg.read()
                delmsg.close()

            try:
                bot.delete_message(chat_id=call.message.chat.id, message_id=int(delmsg_id))
            except:
                pass

            try:
                os.remove(userdir + str(call.message.chat.id) + '/delmsg.id')
            except:
                pass

        # если нажата кнопка информации в расписании
        if call.data == 'pressed_info':
            text_out = '❓ Что означают значки в расписании занятий:\n\n' + \
                u'\u0031\ufe0f\u20e3' + ' - номер пары\n' + \
                u'💬' + ' - лекция\n' + \
                u'🔥' + ' - практика, лаба\n' + \
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
            except:
                bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                 reply_markup=keyboard)

        # если нажата кнопка пар в расписании
        if call.data == 'pressed_time':
            text_out = '🕘 Расписание пар.\n\n' + \
                       '🔹 *ПОНЕДЕЛЬНИК - ПЯТНИЦА:*\n'
            for item in in_rasp_time.items():
                if '1' in item[0]: text_out = text_out + u'\u0031\ufe0f\u20e3'
                if '2' in item[0]: text_out = text_out + u'\u0032\ufe0f\u20e3'
                if '3' in item[0]: text_out = text_out + u'\u0033\ufe0f\u20e3'
                if '4' in item[0]: text_out = text_out + u'\u0034\ufe0f\u20e3'
                if '5' in item[0]: text_out = text_out + u'\u0035\ufe0f\u20e3'
                if '6' in item[0]: text_out = text_out + u'\u0036\ufe0f\u20e3'
                if '7' in item[0]: text_out = text_out + u'\u0037\ufe0f\u20e3'
                if '8' in item[0]: text_out = text_out + u'\u0038\ufe0f\u20e3'
                if '9' in item[0]: text_out = text_out + u'\u0039\ufe0f\u20e3'
                text_out = text_out + ' ' + item[1] + '\n'

            text_out = text_out + '\n🔹 *СУББОТА:*\n'
            for item in in_rasp_time_vih.items():
                if '1' in item[0]: text_out = text_out + u'\u0031\ufe0f\u20e3'
                if '2' in item[0]: text_out = text_out + u'\u0032\ufe0f\u20e3'
                if '3' in item[0]: text_out = text_out + u'\u0033\ufe0f\u20e3'
                if '4' in item[0]: text_out = text_out + u'\u0034\ufe0f\u20e3'
                if '5' in item[0]: text_out = text_out + u'\u0035\ufe0f\u20e3'
                if '6' in item[0]: text_out = text_out + u'\u0036\ufe0f\u20e3'
                if '7' in item[0]: text_out = text_out + u'\u0037\ufe0f\u20e3'
                if '8' in item[0]: text_out = text_out + u'\u0038\ufe0f\u20e3'
                if '9' in item[0]: text_out = text_out + u'\u0039\ufe0f\u20e3'
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
            except:
                bot.send_message(chat_id=call.message.chat.id, text=text_out,
                                 reply_markup=keyboard, parse_mode='Markdown')

    # если пользователь скинул боту что-то, что боту не нужно - удалим это из чата
    @bot.message_handler(content_types=['sticker', 'text', 'location', 'photo', 'document'])
    def any_msg(message):
        logcheck(t_user_id = message.from_user.id)

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
            # print(e)  # или просто print(e) если у вас логгера нет,
            # или import traceback; traceback.print_exc() для печати полной инфы
            traceback.print_exc()
            # time.sleep(1)

        time.sleep(1)

def timecheck():
    global timing, week_id, bot, in_groups

    while True:
        if time.time() - timing > 300:
            timing = time.time()
            nowtime = datetime.now()
            store_back = pd.read_hdf('in_week.h5', week_id)
            loadin()
            store_now = pd.read_hdf('in_week.h5', week_id)
            df_diff = pd.concat([store_back, store_now]).drop_duplicates(keep=False)

            if (not store_now.equals(store_back)) and (nowtime.hour >= 7) and (nowtime.hour <= 21) :
                for subdir, dirs, files in os.walk(userdir):
                    for file in files:
                        if 'config' in file:
                            try:
                                user_id = subdir.replace(userdir, '')
                                with open(userdir + str(user_id) + '/config', "r") as udata:
                                    user_conf = ast.literal_eval(udata.read())
                                    udata.close()

                                if user_conf['warning_on_rasp_change'] == 1:
                                    for dif_group in df_diff['Группа']:
                                        if dif_group == in_groups[str(user_conf['group_id'])]:

                                            text_out2 = '*⚠ Произошли изменения в расписании! ⚠*'

                                            keyboard = types.InlineKeyboardMarkup(keyboard=None, row_width=1)
                                            key_del = types.InlineKeyboardButton(text='♻ Закрыть уведомление ♻',
                                                                                  callback_data='pressed_del')
                                            keyboard.add(key_del)

                                            try:
                                                botmsg = bot.send_message(chat_id=int(user_id), text=text_out2,
                                                                 reply_markup=keyboard, parse_mode='Markdown')

                                                try:
                                                    os.remove(userdir + user_id + '/delmsg.id')
                                                except:
                                                    pass

                                                delmsgu = open(userdir + user_id + '/delmsg.id', "w+")
                                                delmsgu.write(str(botmsg.message_id))
                                                delmsgu.close()

                                            except:
                                                pass

                                            break
                            except:
                                pass

                            time.sleep(60)

        time.sleep(5)

# функция для "заполнения" списков со страницы сайта, нужно вызывать переодически, ибо данные на странице меняются
def loadin():
    # переменные должны быть глобальными, чтобы их содержимое было доступно в отладчике
    global soup, raw_input, in_groups, in_teachers, in_dates, in_places, in_rasp_time, in_rasp_time_vih, in_week, week_id

    try:
        # методом HTTP.POST забираем нужную страницу с сайта
        raw_input = requests.post('https://sarfti.ru/?page_id=20', data={'page_id': '20', 'view': 'Просмотр'}).text
        # разбираем страницу
        soup = BeautifulSoup(raw_input, 'lxml')
        # во временные переменные загоняем данные из таблиц <td></td> с указанными тегами
        groups = [i.findAll('option') for i in soup.findAll('select', attrs = {'name': 'group_id'})]
        teachers = [i.findAll('option') for i in soup.findAll('select', attrs = {'name': 'teacher_id'})]
        places = [i.findAll('option') for i in soup.findAll('select', attrs = {'name': 'place_id'})]
        dates = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'date_id'})]

        for item in soup.findAll('table', attrs={'style': 'width: 274px; border-style: none;'}):
                in_rasp_time = dict(x.split('=') for x in item.text.replace('\n\n\n1 пара','1 пара').replace('\xa0', ' ').replace('\n\n\n', ';').replace('\n–\n', '=').replace('\n', ' | ')[:-1].split(';'))
                break
        for item in soup.findAll('table', attrs={'style': 'width: 273px; border: none;'}):
                in_rasp_time_vih = dict(x.split('=') for x in item.text.replace('\n\n\n1 пара','1 пара').replace('\xa0', ' ').replace('\n\n\n', ';').replace('\n–\n', '=').replace('\n', ' | ')[:-1].split(';'))
                break

        # прогоняем цикл по всем переменным выше, заполняя списки
        for item in [groups, teachers, places, dates]:
            # прогоняем цикл по всем элементам
            for i in range (0, item[0].__len__()):
                # если елемент не содержит "Выберите", то загоняем его в список
                if 'Выберите' not in item[0][i].text:
                    # если разбираем елементы из временной переменной groups
                    if item == groups: in_groups[item[0][i].attrs['value']] = item[0][i].text
                    # если разбираем елементы из временной переменной teachers
                    if item == teachers: in_teachers[item[0][i].attrs['value']] = item[0][i].text
                    # если разбираем елементы из временной переменной places
                    if item == places: in_places[item[0][i].attrs['value']] = item[0][i].text
                    # если разбираем елементы из временной переменной dates
                    if item == dates: in_dates[item[0][i].attrs['value']] = item[0][i].text
                    # условия выше загнаны в один цикл, для экономии ресурсов

        # удаляем временные переменные из памяти, они нам больше не нужны
        del groups, teachers, places, dates, i, item

        # определяем рабочую неделю
        now = datetime.now()
        for week in list(in_dates):
            if now >= pd.to_datetime(in_dates[week]) - timedelta(days=1) and now < pd.to_datetime(in_dates[week]) + timedelta(days=7):
                current_week = pd.to_datetime(in_dates[week]).strftime('%Y-%m-%d')
                week_id = week
                break

        # методом HTTP.POST забираем нужную страницу с сайта
        answer = requests.post('http://scs.sarfti.ru/login/index',
                               data={'login': '', 'password': '', 'guest': 'Войти+как+Гость'})

        traw_input = requests.post('http://scs.sarfti.ru/date/printT',
                                   data={'id': week_id, 'show': 'Распечатать', 'list': 'list',
                                         'compact': 'compact'},
                                   cookies=answer.history[0].cookies)
        traw_input.encoding = 'utf-8'


        # разбираем страницу
        pdtemp = pd
        for item in pdtemp.read_html(StringIO(traw_input.text)):
            if 'День' and 'Пара' in item:
                try:
                    os.remove('in_week.h5')
                except:
                    pass
                store = pd.HDFStore('in_week.h5')
                store[week_id] = item
                store.close()
                in_week = item
                break
    except:
        pass

# функция показа основного меню
def send_main_menu(t_user_id, t_chat_id, t_message_id):
    global menu_1, key_list_0, user_config

    # если есть какие-то "метки" для навигации по меню бота - удаляем, так как вызван режим "всё сначала"
    fileList = glob.glob(userdir + str(t_user_id) + '/step*')
    for filePath in fileList:
        try:
            os.remove(filePath)
        except:
            print(log_dt + ": Error while deleting file : ", filePath)

    # создадим метку, что пользователь в корневом меню бота
    f = open(userdir + str(t_user_id) + '/stepm', "w+")
    f.write('1')
    f.close()

    menu_1 = {1: '👥 Выбрать группу', 2: '📅 Расписание', 3: '🔕 Уведомление [выкл]'}
    try:
        test = '👥 ' + user_config['group_id']
    except:
        user_info_read(t_user_id)

    if user_config['group_id'] != None:
        try:
            menu_1[1] = '👥 ' + in_groups[str(user_config['group_id'])]
        except:
            menu_1[1] = '👥 Выбрать группу'
    else:
        menu_1[1] = '👥 Выбрать группу'

    if user_config['warning_on_rasp_change'] == (0 | 1) and user_config['warning_on_rasp_change'] != None:
        if user_config['warning_on_rasp_change'] == 0: menu_1[3] = '🔕 Уведомление [выкл]'
        if user_config['warning_on_rasp_change'] == 1: menu_1[3] = '🔔 Уведомление [вкл]'
    else:
        menu_1[3] = '🔕 Уведомление [выкл]'
    key_list_0 = {}
    for i in range (1, menu_1.__len__() + 1):
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
    except:
        bot.send_message(chat_id=t_chat_id,
                         text=text_out, reply_markup=keyboard)

# функция чтения конфига пользователя
def user_info_read(t_user_id):
    global user_config
    if os.path.exists(userdir + str(t_user_id) + '/config'):
        try:
            with open(userdir + str(t_user_id) + '/config', "r") as data:
                user_config = ast.literal_eval(data.read())
                data.close()
        except:
            os.remove(userdir + str(t_user_id) + '/config')
            f = open(userdir + str(t_user_id) + '/config', "w+")
            f.write("{'group_id':'', 'warning_on_rasp_change':0, 'c':0, 'd':0}")
            f.close()
            with open(userdir + str(t_user_id) + '/config', "r") as data:
                user_config = ast.literal_eval(data.read())
                data.close()
    else:
        f = open(userdir + str(t_user_id) + '/config', "w+")
        f.write("{'group_id':'', 'warning_on_rasp_change':0, 'c':0, 'd':0}")
        f.close()
        with open(userdir + str(t_user_id) + '/config', "r") as data:
            user_config = ast.literal_eval(data.read())
            data.close()

# функция логирования и проверки каталога пользователя
def logcheck(t_user_id):
    global log_dt
    # берем время/дату для лога
    log_dt = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # если нет каталога для подкаталогов пользователей, то создадим его
    if not os.path.isdir(userdir):
        os.mkdir(userdir)

    # если нет каталога пользователя, то создадим его
    if not os.path.isdir(userdir + str(t_user_id)):
        os.mkdir(userdir + str(t_user_id))

# функция удаления эелементов из чата
def remove_message(t_user_id, t_message_id):
    print(log_dt + ': reg user (' + str(t_user_id) + ') remove message from chat')
    try:
        bot.delete_message(chat_id=t_user_id, message_id=t_message_id)
    except:
        print(log_dt + ': reg user (' + str(t_user_id) + ') error remove message from chat')

# вызов тела скрипта, точка входа
if __name__ == '__main__':
    main()
