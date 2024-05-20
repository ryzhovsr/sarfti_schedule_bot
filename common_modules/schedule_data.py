import contextlib
import os
import pickle
import pandas as pd
import requests

from datetime import datetime, timedelta
from io import StringIO
from bs4 import BeautifulSoup
import math


# ВНИМАНИЕ: требуется наличие библиотеки lxml


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
        self.__temp_week_ids = []  # временная переменная для последующей замены основной
        self.__schedule_current_week = {}  # Расписание текущей (рабочей) недели
        self.__temp_schedule_current_week = {}  # временная переменная для последующей замены основной
        self.__schedule_week_dir = ''  # Путь к директории для файла с расписанием
        self.__schedule_week_file_name = 'schedule_week'

        self.__class_time_weekdays = {}  # Время учебных занятий в будни (понедельник – пятница)
        self.__class_time_saturday = {}  # Время учебных занятий в субботу

        self.__html_data_sarfti_schedule = ''  # Страница расписания СарФТИ c исходным html кодом
        self.__html_soup_sarfti_schedule = ''  # Разобранная html страница расписания СарФТИ

        self.schedule_management_html = None  # Страница для использования хэш данных

        # Смотрим под чем исполняется скрипт, и указываем правильный путь
        if os.name == 'nt':
            self.__schedule_week_dir = os.path.join(os.getcwd(), directory + '\\', 'data\\')
        else:
            self.__schedule_week_dir = os.path.join(os.getcwd(), directory + '/', 'data/')

        self.update_schedule()

    def get_notification(self, user_selection_list_note_one: list):
        """Возвращает сформированный список уведомлений, в формате"""
        # сохраняем данные в переменные для сравнения
        old_current_week_id = self.__current_week_id
        old_last_weeks_id = self.__week_ids

        with (open(self.__schedule_week_dir + self.__schedule_week_file_name + '_' + old_current_week_id + '.pkl', "rb")
              as file):
            old_current_schedule = pickle.load(file)

        # обновление расписания
        self.update_schedule()

        # Проверка на необходимость сопоставление расписаний
        list_notification = [None, False]

        # # FOR TEST для проверки появления новой недели
        # # для проверки на появление новой недели
        # self.__current_week_id = str(int(old_current_week_id) + 1)
        # del old_last_weeks_id[1]
        # # для проверки окончания учебы с удалением расписания всех недель
        # self.__current_week_id = str(int(old_current_week_id) + 1)
        # self.__week_ids = []
        # # END TEST

        # Проверка, что изменения произошли на текущей неделе
        if old_current_week_id == self.__current_week_id:
            if (len(old_last_weeks_id) == len(self.__week_ids)) and (len(self.__week_ids) != 0):
                # проверка на одинаковое ли расписание на текущей неделе
                if not old_current_schedule.equals(self.__schedule_current_week[self.__current_week_id]):
                    list_notification[0] = self.__check_changes(old_current_schedule, user_selection_list_note_one)

            elif len(old_last_weeks_id) < len(self.__week_ids):
                # проверка на одинаковое ли расписание на текущей неделе
                if not old_current_schedule.equals(self.__schedule_current_week[self.__current_week_id]):
                    list_notification[0] = self.__check_changes(old_current_schedule, user_selection_list_note_one)

                list_notification[1] = True

        else:
            if (len(old_last_weeks_id) - 1 == len(self.__week_ids)) and (len(self.__week_ids) != 0):
                pass

            elif len(old_last_weeks_id) - 1 < len(self.__week_ids):
                list_notification[1] = True

        return list_notification

    def __check_changes(self, old_current_schedule, selects_users):
        """Возвращает список групп и преподавателей кого нужно уведомить по первому уведомлению"""
        # проверка на различия двух расписаний
        difference_schedule = (pd.concat([self.__schedule_current_week[self.__current_week_id], old_current_schedule]).
                               drop_duplicates(keep=False))

        list_notification = []
        for column in ['Группа', 'Преподаватель']:
            for dif_group in difference_schedule[column].unique():
                if dif_group in selects_users:
                    list_notification.append(dif_group)

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
            for i in range(1, teachers_raw_data[0].__len__()):
                if (not teachers_raw_data[0][i].text.startswith('Аа')) and (teachers_raw_data[0][i].text[-6] != '-'):
                    self.__teachers[teachers_raw_data[0][i].attrs['value']] = teachers_raw_data[0][i].text

            temp_dates = {}  # Временная переменная для хранения всех недель, необходима для сортированного списка
            for i in range(0, dates_raw_data[0].__len__()):
                temp_dates[dates_raw_data[0][i].attrs['value']] = dates_raw_data[0][i].text
            self.__dates = temp_dates

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
        self.__temp_week_ids = []
        for week_id in list(self.__dates):
            self.__temp_week_ids.append(week_id)
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
                self.__temp_schedule_current_week[week_id] = item
                break

    def update_schedule(self):
        """Обновляет расписание"""
        self.__load_main_data()
        self.__cal_current_week()
        self.__load_schedule()

        # Замена основных данных на новые
        self.__week_ids = self.__temp_week_ids
        self.__schedule_current_week = self.__temp_schedule_current_week
        # Очистка временных файлов
        self.__temp_week_ids = []
        self.__temp_schedule_current_week = {}

    def __del_store(self):
        """Удаление всех старых файлов с расписанием"""
        with contextlib.suppress(Exception):
            for filename in os.listdir(self.__schedule_week_dir):
                if filename != 'users.db' and filename != 'user_actions.txt':
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
        for week in self.__temp_week_ids:
            self.__parse_schedule_week(week)
        self.schedule_management_html = None

    def __get_week_schedule_all(self, week_id):
        """Возвращает расписание на заданную неделю"""
        return self.__schedule_current_week[str(week_id)]

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
                return out_text + '\n' + 'Пар на этой неделе нет!'
            else:
                lessons = self.__form_schedule_teacher(lesson.iterrows(), special_star, special_slash)
        elif output_type == 'Группа':
            lesson = loaded_table.query(f'Группа == @target')
            if lesson.empty:
                return out_text + '\n' + 'Пар на этой неделе нет!'
            else:
                lessons = self.__form_schedule_group(lesson.iterrows(), special_star, special_slash)
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

    def __get_line_schedule_teacher(self, num_lesson, place, groups, lesson, lesson_type, special_slash, subgroup):
        """Возвращает формализованную строку для преподавателя"""

        text_subgroup = ""

        if subgroup == 1:
            text_subgroup = f"{special_slash}[1 пг.] "
        elif subgroup == 1:
            text_subgroup = f"{special_slash}[2 пг.] "

        if groups.find("_") != -1:
            groups_copy = groups
            groups = ""
            for char in groups_copy:
                if char == "_":
                    groups += f"/"
                else:
                    groups += char

        lesson = self.__reduction_lesson(lesson)

        return (f"{self.__get_num_lesson(num_lesson)} {self.__get_emoji(lesson_type)} {lesson}\n"
                f"\u0020\u0020\u0020\u0020\u0020\u0020{special_slash}[{self.__get_place(place)}] {text_subgroup}{groups}\n")

    def __get_line_schedule_group(self, num_lesson, place, teacher, lesson, lesson_type, special_slash, subgroup):
        """Возвращает формализованную строку для группы"""
        text_subgroup = ""

        if subgroup == 1:
            text_subgroup = f"{special_slash}[1 пг.] "
        elif subgroup == 1:
            text_subgroup = f"{special_slash}[2 пг.] "

        lesson = self.__reduction_lesson(lesson)
        place = self.__reduction_place(str(place))

        return (f"{self.__get_num_lesson(num_lesson)} {self.__get_emoji(lesson_type)} {lesson}\n"
                f"\u0020\u0020\u0020\u0020\u0020\u0020{special_slash}[{self.__get_place(place)}] {text_subgroup}{teacher}\n")

    @staticmethod
    def __reduction_place(place: str) -> str:
        if place.find("читальн.") != -1:
            return "к4,чит.зал"
        else:
            return place

    @staticmethod
    def __reduction_lesson(lesson: str) -> str:
        """Возвращает сокращенную строку предмета"""
        step = "\u0020\u0020\u0020\u0020\u0020\u0020"
        match lesson:
            case "Элективные курсы по физической культуре":
                return "Эл. курсы по физ. культуре"
            case "Теория функции комплексной переменной":
                return ("Теория функции комплексной"
                        f"\n{step}переменной")
            case "Классическая теоретическая механика":
                return "Классическая теор. механика"
            case "Уравнения математической физики":
                return "Уравнения мат. физики"
            case "Инновационная экономика и технологическое предприним./Бизнес-планирование научной деятельности":
                return "Инновационная экономика\n"\
                       f"{step}и технологическое предприним./\n"\
                       f"{step}Бизнес-план. науч. деятельности"
            case "Патентоведение в информационных технологиях":
                return ("Патентоведение в инф.\n"
                        f"{step}технологиях")
            case "Лицензирование, стандартизация, сертификация программных средств и информационных технологий":
                return ("Лицензир., стандартиз.,\n"
                        f"{step}сертификация программных\n"
                        f"{step}средств и инф. технологий")
            case "Иностранный язык для профессиональной коммуникации":
                return ("Иностранный язык для\n"
                        f"{step}проф. коммуникации")
            case "Системы искусственного интеллекта":
                return "Системы ИИ"
            case "Численные методы теории переноса":
                return ("Численные методы теории\n"
                        f"{step}переноса")
            case "Методы распараллеливания задач математической физики":
                return ("Методы распараллеливания\n"
                        f"{step}задач мат. физики")
            case "Современные проблемы прикладной математики и информатики.":
                return ("Современные проблемы\n"
                        f"{step}прикладной математики и\n"
                        f"{step}информатики")
            case "Разностные схемы решения многомерных уравнений механики сплошной среды в эйлеровых переменных":
                return ("Разностные схемы решения\n"
                        f"{step}уравнений механики сплошной\n"
                        f"{step}среды в эйлеровых переменных")
            case "Современные компьютерные технологии":
                return "Совр. комп. технологии"
            case "Численные методы газовой динамики":
                return "Числ. методы газ. динамики"
            case "Решение прикладных задач механики сплошных сред на высокопроизводительных ЭВМ":
                return ("Решение прикладных задач\n"
                        f"{step}механики сплошных сред на\n"
                        f"{step}высокопроизводительных ЭВМ")
            case "Математическое моделирование задач механики сплошных сред на высокопроизводительных ЭВМ":
                return ("Мат. моделирование задач\n"
                        f"{step}механики сплошных сред на\n"
                        f"{step}высокопроизводительных ЭВМ")
            case "Этика.Духовно-нравственные ценности отечественной культуры":
                return ("Этика. Духовно-нравственные\n"
                        f"{step}ценности отеч. культуры")
            case "Этика/Духовно-нравственные ценности отечеств. культуры":
                return ("Этика. Духовно-нравственные\n"
                        f"{step}ценности отеч. культуры")
            case "Технологии прототипирования (Робототехника)":
                return ("Технологии прототип.\n"
                        f"{step}(Робототехника)")
            case "Технический английский язык":
                return "Технический англ. язык"
            case "Методы и средства проектирования информационных систем и технологий":
                return ("Методы и средства\n"
                        f"{step}проектирования инф. систем\n"
                        f"{step}и технологий")
            case _:
                if len(lesson) <= 25:
                    return lesson
                else:
                    # return "\n      Электронного документооборота" 29
                    result_text = ""
                    line = ""
                    step = "\u0020\u0020\u0020\u0020\u0020\u0020"
                    words = lesson.split()
                    limit = 25

                    # Флаг для всех строк, кроме первой
                    is_other_row = False

                    for word in words:
                        # Если длина строка равна нулю и следующее слово помещается в строку
                        if len(line) == 0 and len(word) - len(step) * is_other_row <= limit:
                            line += word
                        elif len(line) + len(word) + 1 - len(step) * is_other_row <= limit:
                            line += " " + word
                        # Делаем новую строку
                        else:
                            line += '\n'
                            is_other_row = True
                            result_text += line
                            line = step + word
                            # На любой строке (кроме первой) лимит длины строки будет 28
                            limit = 28

                        # Если это слово последнее
                        if words[-1] == word:
                            result_text += line

                    return result_text

    @staticmethod
    def is_nan(value):
        try:
            return math.isnan(float(value))
        except ValueError:
            return False

    @staticmethod
    def __get_num_lesson(num_lesson):
        """Возвращает номер пары в виде эмодзи"""
        return chr(0x0030 + num_lesson) + '\uFE0F' + chr(0x20E3)

    def __get_place(self, place):
        if self.is_nan(place):
            return 'неизвестно'
        else:
            return place

    @staticmethod
    def __get_full_day_name(user_day, special_star):
        """Возвращает полное название дня недели"""
        full_days = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА', 'ВОСКРЕСЕНЬЕ']
        days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СУБ', 'ВС']
        return '\n🔹 {}{}:{}\n'.format(special_star, full_days[days.index(user_day)], special_star)

    @staticmethod
    def __get_emoji(lesson_type):
        if lesson_type == 'Лекция':
            return u'💬'
        elif lesson_type == 'Практика':
            return u'📝'
        elif lesson_type.startswith('Лаб'):
            return u'🔬'
        elif lesson_type == 'Экзамен':
            return 'Экзамен.'
        elif lesson_type == 'Консультация':
            return 'Консультация.'

    def __form_schedule_teacher(self, table, special_star, special_slash):
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

                    out_text = out_text + self.__get_line_schedule_teacher(prev_row['Пара'],
                                                                           prev_row['Аудитория'],
                                                                           list_groups,
                                                                           prev_row['Предмет'],
                                                                           prev_row['Тип'],
                                                                           special_slash,
                                                                           prev_row['Подгруппа'])
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
                                                               special_slash,
                                                               prev_row['Подгруппа'])
        return out_text

    def __form_schedule_group(self, table, special_star, special_slash):
        """Возвращает текст расписания для группы"""
        index, prev_row = next(table)
        prev_day = str(prev_row['День'])

        out_text = self.__get_full_day_name(prev_row['День'], special_star)
        # repeat = False
        while True:
            try:
                index, row = next(table)
                out_text = out_text + self.__get_line_schedule_group(prev_row['Пара'],
                                                                     prev_row['Аудитория'],
                                                                     prev_row['Преподаватель'],
                                                                     prev_row['Предмет'],
                                                                     prev_row['Тип'],
                                                                     special_slash,
                                                                     prev_row['Подгруппа'])

                # # Заготовка на случай изменение политики нумерации подгрупп
                # if (row['Пара'] == prev_row['Пара']) and (str(row['День']) == prev_day):
                #     # Запись пары как первой подгруппы
                #     repeat = True
                # elif repeat:
                #     # Запись пары как второй подгруппы
                #     repeat = False
                # else:
                #     # Запись пары без подгруппы
                #     pass

                if str(row['День']) != prev_day:
                    out_text = out_text + self.__get_full_day_name(row['День'], special_star)

                prev_day = str(row['День'])
                prev_row = row

            except StopIteration:
                break
        out_text = out_text + self.__get_line_schedule_group(prev_row['Пара'],
                                                             prev_row['Аудитория'],
                                                             prev_row['Преподаватель'],
                                                             prev_row['Предмет'],
                                                             prev_row['Тип'],
                                                             special_slash,
                                                             prev_row['Подгруппа'])
        return out_text


if __name__ == "__main__":
    schedule = ScheduleData()
    # schedule._cal_current_week()
    # schedule.update_schedule()
    # print(schedule.get_week_schedule_group('ЦТ-40', 1))
    # print(schedule.get_week_schedule_teacher('Федоренко Г.А.'))
    # print(schedule.get_week_schedule_group('ЦТ-40'))
    # print(schedule.get_week_schedule_place('к2,117', 1))

    # schedule.get_week_schedule('Группа', 'АВТ-13')
    # print(schedule.get_week_schedule(0)) # вытаскивание расписание недели
    # print(schedule.get_week_schedule(1))
    # print(schedule.get_week_schedule(2))
    # print(schedule.get_week_schedule(3))
    # print(schedule.get_week_schedule(4))
