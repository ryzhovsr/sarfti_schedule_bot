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
from datetime import datetime, timedelta
from telebot import types
from io import StringIO
import contextlib

import warnings
from tables import NaturalNameWarning
warnings.filterwarnings('ignore', category=NaturalNameWarning)

locale.setlocale(locale.LC_ALL, '')

# объявляем переменные
in_groups = {}  # список групп и их group_id
in_teachers = {}  # список преподавателей и их teacher_id
in_places = {}  # список аудиторий и их place_id
in_dates = {}  # список учебных недель и их date_id
in_week = {}  # таблица с расписанием текущей недели
week_id = ''  # id текущей недели
# все списки выше необходимы для работы бота в режиме "выбор группы/преподавателей/недели/аудитории"
soup = ''  # разобранная страница
raw_input = ''  # неразобранная страница
# обе переменных нужны для отладки приложения, так все первичные данные
v_version = '22.07.22'  # версия скрипта
c_token = ''  #
config = configparser.ConfigParser()  # создаем переменную-парсер нашего конфиг файла
config.read('bot.ini', encoding="utf-8")  # читаем конфиг
bot_token = str(config['set']['token'])  # берём токен для работы bot.api
# c_admin_list = [int(x) for x in config.get('set', 'admin_list').split(',')]
bot = telebot.TeleBot(bot_token, threaded=False)  # создаем/регистрируем бота
user_dir = ''  # переменная для пути к каталогу пользователей
menu_1 = {}  # переменная для хранения главного меню
key_list_groups = {}  # переменная для хранения списка групп
user_config = {}  # переменная для хранения данных конфига пользователя
in_rasp_time = {}
in_rasp_time_vih = {}
key_list_0 = ''
log_dt = ''

# здесь хитрость: смотрим, под чем исполняется скрипт, и указываем правильные пути
if os.name == 'nt':
    user_dir = os.path.join(os.getcwd(), 'users\\')
else:
    user_dir = os.path.join(os.getcwd(), 'users/')

# инициализируем таймер
timing = time.time()


# описываем функции
# тело скрипта
def main():
    # здесь описываем реакции бота на действия пользователя

    # заполняем списки (вызывать периодически, по событию или таймеру)
    loadin()
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

                key_list_groups = [] * in_groups.__len__()
                i = 1
                for key_i in in_groups:
                    key_list_groups[i - 1] = types.InlineKeyboardButton(text=in_groups[key_i],
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
                for group in in_groups:
                    if group == str(user_config['group_id']):
                        group = in_groups[group]
                        break

                if group == '':
                    text_out = 'Выберите группу'
                else:
                    text_out = '*📅 ' + pd.to_datetime(in_dates[week_id]).strftime('%d %B') + ' - ' + \
                               (pd.to_datetime(in_dates[week_id]) + timedelta(days=7)).strftime('%d %B %Yг') + '*\n'

                    day_f = False
                    day_prev = ''

                    for index, row in pd.read_hdf('in_week.h5', week_id).query('Группа == @group').iterrows():
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
                    user_config['group_id'] = list(in_groups.keys())[x - 1]
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
            for item in in_rasp_time.items():
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
            for item in in_rasp_time_vih.items():
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
    global timing, week_id, bot, in_groups

    while True:
        if time.time() - timing > 300:
            timing = time.time()
            now_time = datetime.now()
            store_back = pd.read_hdf('in_week.h5', week_id)
            loadin()
            store_now = pd.read_hdf('in_week.h5', week_id)
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
                                        if dif_group == in_groups[str(user_conf['group_id'])]:

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


# функция для "заполнения" списков со страницы сайта, нужно вызывать периодически, ибо данные на странице меняются
def loadin():
    # переменные должны быть глобальными, чтобы их содержимое было доступно в отладчике
    global soup, raw_input, in_groups, in_teachers, in_dates, in_places, in_week, week_id, in_rasp_time, \
        in_rasp_time_vih

    try:
        # методом HTTP.POST забираем нужную страницу с сайта
        raw_input = requests.post('https://sarfti.ru/?page_id=20', data={'page_id': '20', 'view': 'Просмотр'}).text
        # разбираем страницу
        soup = BeautifulSoup(raw_input, 'lxml')
        # во временные переменные загоняем данные из таблиц <td></td> с указанными тегами
        groups = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'group_id'})]
        teachers = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'teacher_id'})]
        places = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'place_id'})]
        dates = [i.findAll('option') for i in soup.findAll('select', attrs={'name': 'date_id'})]

        for item in soup.findAll('table', attrs={'style': 'width: 274px; border-style: none;'}):
            in_rasp_time = dict(x.split('=') for x in item.text.replace('\n\n\n1 пара', '1 пара').
                                replace('\xa0', ' ').replace('\n\n\n', ';').
                                replace('\n–\n', '=').replace('\n', ' | ')[:-1].split(';'))
            break
        for item in soup.findAll('table', attrs={'style': 'width: 273px; border: none;'}):
            in_rasp_time_vih = dict(x.split('=') for x in
                                    item.text.replace('\n\n\n1 пара', '1 пара').
                                    replace('\xa0', ' ').replace('\n\n\n', ';').
                                    replace('\n–\n', '=').replace('\n', ' | ')[:-1].split(';'))
            break

        # прогоняем цикл по всем переменным выше, заполняя списки
        for item in [groups, teachers, places, dates]:
            # прогоняем цикл по всем элементам
            for i in range(0, item[0].__len__()):
                # если элемент не содержит "Выберите", то загоняем его в список
                if 'Выберите' not in item[0][i].text:
                    # если разбираем элементы из временной переменной groups
                    if item == groups:
                        in_groups[item[0][i].attrs['value']] = item[0][i].text
                    # если разбираем элементы из временной переменной teachers
                    if item == teachers:
                        in_teachers[item[0][i].attrs['value']] = item[0][i].text
                    # если разбираем элементы из временной переменной places
                    if item == places:
                        in_places[item[0][i].attrs['value']] = item[0][i].text
                    # если разбираем элементы из временной переменной dates
                    if item == dates:
                        in_dates[item[0][i].attrs['value']] = item[0][i].text
                    # условия выше загнаны в один цикл, для экономии ресурсов

        # удаляем временные переменные из памяти, они нам больше не нужны
        del groups, teachers, places, dates, i, item

        # определяем рабочую неделю
        now = datetime.now()
        for week in list(in_dates):
            if (pd.to_datetime(in_dates[week]) - timedelta(days=1) <= now <
                    pd.to_datetime(in_dates[week]) + timedelta(days=7)):
                # current_week = pd.to_datetime(in_dates[week]).strftime('%Y-%m-%d')
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
        pd_temp = pd
        for item in pd_temp.read_html(StringIO(traw_input.text)):
            if 'День' and 'Пара' in item:
                try:
                    os.remove('in_week.h5')
                except Exception as e:
                    print(e)
                    pass
                store = pd.HDFStore('in_week.h5')
                store[week_id] = item
                store.close()
                in_week = item
                break
    except Exception as e:
        print(e)
        pass


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

    try:
        test = '👥 ' + user_config['group_id']
        print(test)
    except Exception as e:
        print(e)
        user_info_read(t_user_id)

    if user_config['group_id'] is not None:
        try:
            menu_1[1] = '👥 ' + in_groups[str(user_config['group_id'])]
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
    except Exception as e:
        print(e)
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


# функция удаления элементов из чата
def remove_message(t_user_id, t_message_id):
    print(log_dt + ': reg user (' + str(t_user_id) + ') remove message from chat')
    try:
        bot.delete_message(chat_id=t_user_id, message_id=t_message_id)
    except Exception as exc:
        print(exc)
        print(log_dt + ': reg user (' + str(t_user_id) + ') error remove message from chat')


# вызов тела скрипта, точка входа
if __name__ == '__main__':
    main()
