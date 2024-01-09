import locale
import threading
import traceback
import warnings
from tables import NaturalNameWarning
import configparser
import telebot
import time
import os
import datetime
from datetime import datetime, timedelta
import glob
import requests
from bs4 import BeautifulSoup
from io import StringIO
import pandas as pd
import contextlib
import ast
from telebot import types


# Все переменные ниже необходимы для работы бота в режиме "выбор группы/преподавателей/недели/аудитории"
in_groups = {}    # Список групп и их group_id
in_teachers = {}  # Список преподавателей и их teacher_id
in_places = {}    # Список аудиторий и их place_id
in_dates = {}     # Список учебных недель и их date_id
in_week = {}      # Таблица с расписанием текущей недели
week_id = ''      # id текущей недели

soup = ''             # Разобранная страница
raw_input = ''        # Неразобранная страница
user_dir = ''         # Переменная для пути к каталогу пользователей
menu_1 = {}           # Переменная для хранения главного меню
key_list_groups = {}  # Переменная для хранения списка групп
user_config = {}      # Переменная для хранения данных конфига пользователя

# Смотрим под чем исполняется скрипт, и указываем правильные пути
if os.name == 'nt':
    user_dir = os.path.join(os.getcwd(), 'users\\')
else:
    user_dir = os.path.join(os.getcwd(), 'users/')

timing = time.time()  # Инициализируем таймер
in_rasp_time = {}
in_rasp_time_vih = {}
key_list_0 = ''
log_dt = ''

config = configparser.ConfigParser()                # Создаем переменную-парсер нашего конфиг файла
config.read('bot.ini', encoding="utf-8")   # Читаем конфиг
bot_token = str(config['set']['bot_token'])         # Берём токен для работы bot.api
bot = telebot.TeleBot(bot_token, threaded=False)    # Создаем/регистрируем бота
admin_list_id = [int(x) for x in config.get('set', 'admin_list').split(',')]  # Список id админов


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
                return user_config
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

