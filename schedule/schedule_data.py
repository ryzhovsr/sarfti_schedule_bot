import contextlib
import os
import pickle
import time
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

import locale

# требуется наличие библиотеки lxml

# TODO: сделать уведомления


class ScheduleData:
    def __init__(self, directory='src_telegram'):
        if directory == 'src_telegram':
            self.__telegram = True
        else:
            self.__telegram = False

        self.__groups = {}  # Группы
        self.__teachers = {}  # Преподаватели
        self.__places = {}  # Аудитории
        self.__dates = {}  # Учебные недели

        self.__current_week_id = ''  # id текущей (рабочей) недели
        self.__week_ids = []  # id всех доступные недель
        self.__schedule_current_week = {}  # Расписание текущей (рабочей) недели
        self.__schedule_week_dir = ''  # Путь к директории для файла с расписанием
        self.__schedule_week_file_name = 'schedule_week'

        self.__class_time_weekdays = {}  # Время учебных занятий в будни (понедельник – пятница)
        self.__class_time_saturday = {}  # Время учебных занятий в субботу

        self.__html_data_sarfti_schedule = ''  # Страница расписания СарФТИ c исходным html кодом
        self.__html_soup_sarfti_schedule = ''  # Разобранная html страница расписания СарФТИ

        self.schedule_management_html = None  # Страница для использования хэш данных

        locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')  # устанавливается русский язык

        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            self.__schedule_week_dir = os.path.join(os.getcwd(), directory + '\\', 'data\\')
        else:
            self.__schedule_week_dir = os.path.join(os.getcwd(), directory + '\\', 'data\\')

        self.update_schedule()

        # from src_telegram.create import user_db
        # user = user_db.get_all_note_current_week()
        # list_user = []
        # for item in user:
        #     list_user.append(item[0])
        # print(list_user)
        # self.get_notification(list_user)

    def get_notification(self, list_user):

        # сохраняем данные в переменные для сравнения
        last_current_week_id = self.__current_week_id
        last_week_id_list = self.__week_ids
        last_schedules = {}
        # for week in last_week_id_list:
        with open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + last_current_week_id + '.pkl',
                  "rb") as file:
            last_schedules[last_current_week_id] = pickle.load(file)

        # обновление расписания
        self.update_schedule()
        print("www")
        list_notification = []
        if last_current_week_id == self.__current_week_id:
            if len(last_week_id_list) == len(self.__week_ids) >= 1:
                print("больше или ровна")
                list_notification.append(self.__check_changes(self.__current_week_id,
                                                              last_schedules[self.__current_week_id], list_user))
                pass

                # цикл по всем неделям self.__week_ids
                # уведомление об изменении на неделях + на текущей недели + на этом дне
            elif len(last_week_id_list) < len(self.__week_ids):
                pass
                # цикл по неделям last_week_id_list
                # уведомление об изменении на неделях (новая неделя) + на текущей недели + на этом дне
            pass
        else:
            if len(last_week_id_list) - 1 == len(self.__week_ids):
                pass
                # цикл по всем неделям self.__week_ids
                # уведомление об изменении на неделях + на текущей недели + на этом дне
            else:
                pass
                # цикл по неделям last_week_id_list
                # уведомление об изменении на неделях (новая неделя) + на текущей недели + на этом дне
            pass

    def __check_changes(self, week, last_schedule, list_user):
        with open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + week + '.pkl', "rb") as file:
            new_schedule = pickle.load(file)

            # проверка на различия двух расписаний
            difference_schedule = pd.concat([new_schedule, last_schedule]).drop_duplicates(keep=False)
            # print(last_schedule['Группа'].iterrows())

            list_notification = []
            # if not difference_schedule.empty:
            # user нужно передать список используемых групп
            for column in ['Группа', 'Преподаватель']:
                for dif_group in difference_schedule[column].unique():
                    if dif_group in list_user:
                        list_notification.append(dif_group)

            # user нужно передать список используемых преподавателей
            # list_user = ['Федоренко Г.А.', 'Марин С.В.']
            # for dif_teacher in difference_schedule['Преподаватель'].unique():
            #     if dif_teacher in list_user:
            #         list_notification.append(dif_teacher)
            print(list_notification)
            return list_notification

    def __load_main_data(self):
        """Парсит списки групп, преподавателей, аудиторий и недель c сайта СарФТИ"""
        with contextlib.suppress(Exception):
            # Берём страницу с расписанием СарФТИ
            self.__html_data_sarfti_schedule = requests.post('https://sarfti.ru/?page_id=20',
                                                             data={'page_id': '20', 'view': 'Просмотр'}).text

            # Разбираем страницу
            self.__html_soup_sarfti_schedule = BeautifulSoup(self.__html_data_sarfti_schedule, 'lxml')

            # Получаем сырые данные групп, преподавателей, мест (аудиторий) и дат
            groups_raw_data = [i.findAll('option') for i in
                               self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'group_id'})]
            teachers_raw_data = [i.findAll('option') for i in
                                 self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'teacher_id'})]
            places_raw_data = [i.findAll('option') for i in
                               self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'place_id'})]
            dates_raw_data = [i.findAll('option') for i in
                              self.__html_soup_sarfti_schedule.findAll('select', attrs={'name': 'date_id'})]

            # Получаем время занятий на будние дни
            for item in self.__html_soup_sarfti_schedule.findAll('table',
                                                                 attrs={'style': 'width: 274px; border-style: none;'}):
                self.__class_time_weekdays = dict(x.split('=') for x in item.text.
                                                  replace('\n\n\n1 пара', '1 пара').
                                                  replace('\xa0', ' ').
                                                  replace('\n\n\n', ';').
                                                  replace('\n–\n', '=').
                                                  replace('\n', ' | ')[:-1].split(';'))
                break

            # Получаем время занятий на субботу
            for item in self.__html_soup_sarfti_schedule.findAll('table',
                                                                 attrs={'style': 'width: 273px; border: none;'}):
                self.__class_time_saturday = dict(x.split('=') for x in item.text.
                                                  replace('\n\n\n1 пара', '1 пара').
                                                  replace('\xa0', ' ').
                                                  replace('\n\n\n', ';').
                                                  replace('\n–\n', '=').
                                                  replace('\n', ' | ')[:-1].split(';'))
                break

            for i in range(1, groups_raw_data[0].__len__()):
                self.__groups[groups_raw_data[0][i].attrs['value']] = groups_raw_data[0][i].text
            for i in range(1, places_raw_data[0].__len__()):
                self.__places[places_raw_data[0][i].attrs['value']] = places_raw_data[0][i].text
            for i in range(0, dates_raw_data[0].__len__()):
                self.__dates[dates_raw_data[0][i].attrs['value']] = dates_raw_data[0][i].text
            for i in range(1, teachers_raw_data[0].__len__()):
                if (not teachers_raw_data[0][i].text.startswith('Аа')) and (teachers_raw_data[0][i].text[-6] != '-'):
                    self.__teachers[teachers_raw_data[0][i].attrs['value']] = teachers_raw_data[0][i].text

            # Прогоняем цикл по всем сырым данным групп, преподавателей, мест (аудиторий) и дат
            # for item in [groups_raw_data, teachers_raw_data, places_raw_data, dates_raw_data]:
            #     for i in range(0, item[0].__len__()):
            #         # Если элемент не содержит "Выберите", то загоняем его в соответствующий список
            #         if 'Выберите' not in item[0][i].text:
            #             if item == groups_raw_data:
            #                 self.__groups[item[0][i].attrs['value']] = item[0][i].text
            #             if item == teachers_raw_data:
            #                 self.__teachers[item[0][i].attrs['value']] = item[0][i].text
            #             if item == places_raw_data:
            #                 self.__places[item[0][i].attrs['value']] = item[0][i].text
            #             if item == dates_raw_data:
            #                 self.__dates[item[0][i].attrs['value']] = item[0][i].text

    def __cal_current_week(self):
        """Вычисляет текущую неделю"""
        time_now = datetime.now()
        self.__week_ids = []
        for week_id in list(self.__dates):
            self.__week_ids.append(week_id)
            if (pd.to_datetime(self.__dates[week_id]) - timedelta(days=1) <= time_now <
                    pd.to_datetime(self.__dates[week_id]) + timedelta(days=7)):
                self.__current_week_id = week_id
                break

    def __parse_schedule_week(self, week_id):
        """Парсит расписание по заданному id недели"""
        # Данные сайта по печати (вывода) расписания на текущую неделю
        current_week_schedule_html = requests.post('http://scs.sarfti.ru/date/printT',
                                                   data={'id': week_id, 'show': 'Распечатать',
                                                         'list': 'list', 'compact': 'compact'},
                                                   cookies=self.schedule_management_html.history[0].cookies)

        current_week_schedule_html.encoding = 'utf-8'

        for item in pd.read_html(StringIO(current_week_schedule_html.text)):
            if 'День' and 'Пара' in item:
                with open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + week_id + '.pkl',
                          "wb") as file:
                    pickle.dump(item, file)
                self.__schedule_current_week = item
                break

    def update_schedule(self):
        """Обновляет расписание"""
        self.__load_main_data()
        self.__cal_current_week()
        self.__load_schedule()

    def __del_store(self):
        """Удаление всех старых файлов с расписанием"""
        with contextlib.suppress(Exception):
            for filename in os.listdir(self.__schedule_week_dir):
                file_path = os.path.join(self.__schedule_week_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)

    def __load_schedule(self):
        """Загружает в файлы расписание для актуальной и более новых недель"""
        self.__del_store()
        # Данные сайта по управлению расписанием
        self.schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                      data={'login': '', 'password': '',
                                                            'guest': 'Войти+как+Гость'})
        for week in self.__week_ids:
            self.__parse_schedule_week(week)
        self.schedule_management_html = None

    def run_updates(self, iterations_between_updates=30, sleep_time=120):
        """Запускает обновление основных данных и парсер расписания
        iterations_between_updates=30 и sleep_time=120 - будет обновляться база каждый день, а расписание каждые 2 мин
        """
        while True:
            self.__load_main_data()
            time.sleep(sleep_time)
            # Данные сайта по управлению расписанием
            self.schedule_management_html = requests.post('http://scs.sarfti.ru/login/index',
                                                          data={'login': '', 'password': '',
                                                                'guest': 'Войти+как+Гость'})
            for i in range(iterations_between_updates):
                self.__parse_schedule_week(self.__load_schedule())
                time.sleep(sleep_time)
            self.schedule_management_html = None

    def __get_week_schedule_all(self, week_id):
        """Возвращает расписание на заданную неделю"""
        with open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + str(week_id) + '.pkl',
                  "rb") as file:
            loaded_table = pickle.load(file)
        return loaded_table

    def get_week_schedule(self, output_type, target, week_id):
        """Возвращает расписание в зависимости от типа расписания и по чему выводить (например, название группы)"""
        if self.__telegram:
            special_star = '*'
            special_slash = '\\'
        else:
            special_star = special_slash = ''

        loaded_table = self.__get_week_schedule_all(week_id)
        months = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня', 'Июля',
                  'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря']
        beginning_week = (pd.to_datetime(self.__dates[str(week_id)]).strftime('%d ') +
                          months[int(pd.to_datetime(self.__dates[str(week_id)]).strftime('%m')) - 1])
        end_date = pd.to_datetime(self.__dates[str(week_id)]) + timedelta(days=7)
        end_week = end_date.strftime('%d ') + months[int(end_date.strftime('%m')) - 1] + end_date.strftime(' %Y г.')
        out_text = '{}{} - {}{}\n'.format(special_star, beginning_week, end_week, special_star)
        out_text += "{}{} {}{}\n".format(special_star, output_type, target, special_star)
        lessons = ''
        if output_type == 'Преподаватель':
            lesson = loaded_table.query(f'Преподаватель == @target')
            if lesson.empty:
                return out_text + '\n' + 'Пар на это неделе нет!'
            else:
                lessons = self.__form_schedule_teacher(lesson.iterrows(), target, special_star, special_slash)
        elif output_type == 'Группа':
            lesson = loaded_table.query(f'Группа == @target')
            if lesson.empty:
                return out_text + '\n' + 'Пар на это неделе нет!'
            else:
                lessons = self.__form_schedule_group(loaded_table, target, special_star, special_slash)
        return out_text + lessons

    def get_week_schedule_group(self, group_name, week_id):
        """Возвращает расписание группы с именем group_name"""
        return self.get_week_schedule('Группа', group_name, week_id)

    def get_week_schedule_teacher(self, teacher_name, week_id):
        """Возвращает расписание группы с именем group_name"""
        return self.get_week_schedule('Преподаватель', teacher_name, week_id)

    def get_week_schedule_place(self, place_name, week_num=0):
        """Возвращает расписание группы с именем group_name"""
        return self.get_week_schedule('Аудитория', place_name, week_num)

    def get_dates(self):
        """Возвращает учебные недели"""
        return self.__dates

    def get_groups(self):
        """Возвращает группы"""
        return self.__groups

    def get_teachers(self):
        """Возвращает преподавателей"""
        return self.__teachers

    def get_schedule_week_dir(self):
        """Возвращает путь к директории для файлов с расписанием, а не путь к файлу"""
        return self.__schedule_week_dir

    def get_class_time_saturday(self):
        """Возвращает время учебных занятий в субботу"""
        return self.__class_time_saturday

    def get_class_time_weekdays(self):
        """Возвращает время учебных занятий в будни (понедельник – пятница)"""
        return self.__class_time_weekdays

    def get_current_week_id(self):
        """Возвращает id текущей недели"""
        return self.__current_week_id

    def get_upcoming_weeks_list(self):
        """Возвращает список будущих недель"""
        # week_id_list = self.__week_ids[0:]
        upcoming_weeks = {}
        for week_id in self.__week_ids[-2::-1]:
            upcoming_weeks[week_id] = (self.__dates[week_id])
        return upcoming_weeks

    def __get_line_schedule_teacher(self, num_lesson, place, groups, lesson, lesson_type, special_slash):
        """Возвращает формализованную строку для преподавателя"""
        return '{}{}{} {}[{}] {} {}\n'.format(self.__get_num_lesson(num_lesson),
                                              self.__get_emoji(lesson_type),
                                              lesson_type,
                                              special_slash,
                                              place,
                                              groups,
                                              lesson)

    def __get_line_schedule_group(self, num_lesson, place, teacher, lesson, lesson_type, special_slash):
        """Возвращает формализованную строку для группы"""
        return '{}{}{} {}[{}] {}, {}\n'.format(self.__get_num_lesson(num_lesson),
                                               self.__get_emoji(lesson_type),
                                               lesson_type,
                                               special_slash,
                                               self.__get_place(place),
                                               lesson,
                                               teacher)

    @staticmethod
    def __get_place(place):
        if 'онлайн' in place.lower():
            return u'📡 ' + place
        else:
            return place

    @staticmethod
    def __get_num_lesson(num_lesson):
        """Возвращает номер пары в виде эмодзи"""
        return chr(0x0030 + num_lesson) + '\uFE0F' + chr(0x20E3)

    @staticmethod
    def __get_full_day_name(user_day, special_star):
        """Возвращает полное название дня недели"""
        full_days = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СУБ', 'ВС']
        return '\n🔹 {}{}:{}\n'.format(special_star, full_days[days.index(user_day)], special_star)

    @staticmethod
    def __get_emoji(lesson_type):
        # TODO: поменять эмодзи подгрупп
        if lesson_type == 'Лекция':
            return u'💬'
        if lesson_type == 'Практика':
            return u'📝'
        if lesson_type.startswith('Лаб'):
            if '1' in lesson_type:
                return u'🔬' + u'➊ '
            if '2' in lesson_type:
                return u'🔬' + u'➋ '
            return u'🔬'
        return u'🔥'

    def __form_schedule_teacher(self, table, target, special_star, special_slash):
        """Возвращает текст расписания для преподавателя"""
        index, prev_row = next(table)
        prev_day = str(prev_row['День'])
        list_groups = prev_row['Группа']

        out_text = self.__get_full_day_name(prev_row['День'], special_star)
        repeat = False
        while True:
            try:
                index, row = next(table)
                if (row['Пара'] == prev_row['Пара']) and (str(row['День']) == prev_day):
                    list_groups = list_groups + ', ' + row['Группа']
                    repeat = True
                else:
                    if not repeat:
                        list_groups = prev_row['Группа']
                        # repeat = False
                    out_text = out_text + self.__get_line_schedule_teacher(prev_row['Пара'],
                                                                           prev_row['Аудитория'],
                                                                           list_groups,
                                                                           prev_row['Предмет'],
                                                                           prev_row['Тип'],
                                                                           special_slash)
                    if str(row['День']) != prev_day:
                        t = self.__get_full_day_name(row['День'], special_star)
                        out_text = out_text + t

                    repeat = False
                    list_groups = row['Группа']

                prev_day = str(row['День'])
                prev_row = row
            except StopIteration:
                break
        out_text = out_text + self.__get_line_schedule_teacher(prev_row['Пара'],
                                                               prev_row['Аудитория'],
                                                               list_groups,
                                                               prev_row['Предмет'],
                                                               prev_row['Тип'],
                                                               special_slash)
        return out_text

    def __form_schedule_group(self, table, target, special_star, special_slash):
        """Возвращает текст расписания для группы"""
        prev_row = ''
        out_text = ''
        for index, row in table.query('Группа == @target').iterrows():
            if prev_row != row['День']:
                out_text = out_text + self.__get_full_day_name(row['День'], special_star)
            out_text = out_text + self.__get_line_schedule_group(row['Пара'],
                                                                 row['Аудитория'],
                                                                 row['Преподаватель'],
                                                                 row['Предмет'],
                                                                 row['Тип'],
                                                                 special_slash)
            prev_row = row['День']
        return out_text


if __name__ == "__main__":
    schedule = ScheduleData()
    # schedule._cal_current_week()
    # schedule.update_schedule()
    # print(schedule.get_week_schedule_group('ЦТ-40', 1))
    # print(schedule.get_week_schedule_teacher('Федоренко Г.А.'))
    print(schedule.get_week_schedule_group('ЦТ-40'))
    # print(schedule.get_week_schedule_place('к2,117', 1))

    # schedule.get_week_schedule('Группа', 'АВТ-13')
    # print(schedule.get_week_schedule(0)) # вытаскивание расписание недели
    # print(schedule.get_week_schedule(1))
    # print(schedule.get_week_schedule(2))
    # print(schedule.get_week_schedule(3))
    # print(schedule.get_week_schedule(4))
