from vkbottle import Keyboard, Callback


class SearchKeyboard:
    def __init__(self):
        self.__dict_books = {}

    def get_keyboard(self, peer_id, coincidence: dict):
        list_pages = []
        number_page = 0

        number_coincidences = len(coincidence)
        search_list = list(coincidence.values())
        button_limit = 6

        if number_coincidences <= button_limit:
            keyboard = Keyboard(inline=True)

            for i in range(number_coincidences):
                keyboard.add(Callback(f"{search_list[i]}", {"current_selection": f"{search_list[i]}"}))

                if (i + 1) % 2 == 0:
                    keyboard.row()

            if number_coincidences % 2 != 0:
                keyboard.row()

            keyboard.add(
                Callback("Вернутся к выбору", {"start_menu": "back"})).get_json()

            list_pages.append(keyboard)

        else:
            count = int(number_coincidences / button_limit)
            modul = number_coincidences % button_limit

            for i in range(count + 1):
                keyboard = Keyboard(inline=True)

                for j in range(button_limit):

                    if i == count and modul != 0 and j == modul:
                        break

                    keyboard.add(Callback(f"{search_list[j + i * button_limit]}",
                                          {"current_selection": f"{search_list[j + i * button_limit]}"}))

                    if (j + 1) % 2 == 0:
                        keyboard.row()

                if modul % 2 != 0 and i == count:
                    keyboard.row()

                if i == 0:
                    keyboard.add(Callback("Следующая ➡️", {"search_menu": "following"})).row()

                elif i == count:
                    keyboard.add(Callback("⬅️ Предыдущая", {"search_menu": "previous"})).row()

                else:
                    keyboard.add(Callback("⬅️ Предыдущая", {"search_menu": "previous"}))
                    keyboard.add(Callback("Следующая ➡️", {"search_menu": "following"})).row()

                keyboard.add(
                    Callback("Вернутся к выбору", {"start_menu": "back"})).get_json()

                list_pages.append(keyboard)

        self.__dict_books[peer_id] = [list_pages, number_page]

        return self.__dict_books[peer_id][0]

    def get_list_pages(self, peer_id):

        return self.__dict_books[peer_id][0]

    def set_page_number(self, peer_id, page_number):

        if page_number <= 0:
            self.__dict_books[peer_id][1] = 0

        elif page_number >= len(self.__dict_books[peer_id][0]) - 1:
            self.__dict_books[peer_id][1] = len(self.__dict_books[peer_id][0]) - 1

        else:
            self.__dict_books[peer_id][1] = page_number

    def get_page_number(self, peer_id):

        return self.__dict_books[peer_id][1]
