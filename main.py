from kivy.config import Config
from concurrent.futures import ThreadPoolExecutor
from itertools import chain

from kivy.metrics import dp
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp

from kivy.uix.stacklayout import StackLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivymd.uix.button import MDRectangleFlatButton, MDRectangleFlatIconButton
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.textfield import MDTextField

from functools import partial
import logging
import re

from threading import Thread
from kivy.clock import Clock

from table_components_functions.start_program import initialize_table
from table_components_functions.utils import IconButtonWithTooltip, BorderedCell


Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "700")
Config.write()


class DataLexApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fragments = {}  # Словарь для хранения фрагментов
        self.files = {}
        self.table_layout = None  # Контейнер для отображения таблицы
        self.original_text = ""  # Переменная для хранения исходного текста
        self.current_fragment_to_remove = None
        self.dialog = None

        # Настройка логгера
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # Уровень логирования (DEBUG для подробных сообщений)

        # Создаем обработчик для записи логов в файл
        handler = logging.FileHandler('app_log.log', encoding='utf-8')
        handler.setLevel(logging.DEBUG)  # Уровень логирования для этого обработчика

        # Создаем формат логов
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Добавляем обработчик в логгер
        self.logger.addHandler(handler)

        self.base_dict_words = []  # Список для слов базового словаря
        self.trash_words = []  # Список для слов корзины

    def build(self):
        self.texts = []
        self.text_area = TextInput(
            text="Нет текста", multiline=True, size_hint=(0.8, 1), readonly=True
        )

        # Основная панель с вкладками
        tb = TabbedPanel(do_default_tab=False, tab_pos="top_left", tab_height=22)

        # Вкладка "Фрагменты"
        fragments_tab = TabbedPanelItem(
            text="Фрагменты", font_size="12sp", size_hint=(None, None), width=50, height=22
        )
        layout = BoxLayout(orientation="vertical", spacing=10, padding=5)

        # Используем StackLayout для кнопок
        buttons_layout = StackLayout(orientation="lr-tb", size_hint_y=None, spacing=10, height=40)
        button1 = IconButtonWithTooltip(
            icon="folder-multiple-plus",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#35C0CD",
            icon_size="10dp",
            tooltip_text="Добавить текстов",
        )
        button1.bind(on_release=self.open_file_dialog)
        button2 = IconButtonWithTooltip(
            icon="content-save",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#35C0CD",
            icon_size="10dp",
            tooltip_text="Сохранить изменения",
        )
        button3 = IconButtonWithTooltip(
            icon="checkbox-marked-circle-outline",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#35C0CD",
            icon_size="10dp",
            tooltip_text="Отметить всё",
        )
        button3.bind(on_release=self.select_all_checkboxes)
        button4 = IconButtonWithTooltip(
            icon="checkbox-marked-circle-minus-outline",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#35C0CD",
            icon_size="10dp",
            tooltip_text="Обратить отмеченное",
        )
        button4.bind(on_release=self.disable_all_checkboxes)
        button5 = IconButtonWithTooltip(
            icon="calculator",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#f2e66b",
            icon_size="10dp",
            tooltip_text="Обработка",
        )
        button5.bind(on_release=self.show_processing_dialog)
        button6 = IconButtonWithTooltip(
            icon="window-close",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#e33d3d",
            icon_size="10dp",
            tooltip_text="Удалить фрагмент",
        )
        button6.bind(on_release=self.delete_selected_fragments)
        button7 = IconButtonWithTooltip(
            icon="code-brackets",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#35C0CD",
            icon_size="10dp",
            tooltip_text="Разделить текст",
        )
        button7.bind(on_release=self.split_text)

        buttons_layout.add_widget(button1)
        buttons_layout.add_widget(button2)
        buttons_layout.add_widget(button3)
        buttons_layout.add_widget(button4)
        buttons_layout.add_widget(button5)
        buttons_layout.add_widget(button6)
        buttons_layout.add_widget(button7)

        # Добавляем кнопки в layout
        layout.add_widget(buttons_layout)

        # Основной лэйаут с таблицей и текстовым полем
        main_layout = BoxLayout(orientation="horizontal", spacing=10)
        self.table_layout = GridLayout(cols=4, size_hint=(0.4, 1), spacing=5)

        # Инициализация таблицы через функцию
        initialize_table(self.table_layout)

        main_layout.add_widget(self.table_layout)
        main_layout.add_widget(self.text_area)

        layout.add_widget(main_layout)

        # Добавляем ProgressBar в самый низ
        self.progress_bar = ProgressBar(max=100, value=0, size_hint_y=None, height=20)
        layout.add_widget(self.progress_bar)

        fragments_tab.add_widget(layout)
        tb.add_widget(fragments_tab)

        # Вкладка "Фильтры"
        filters_tab = TabbedPanelItem(
            text="Фильтры", font_size="12sp", size_hint=(None, None), width=50, height=22
        )
        filters_tab.add_widget(Label(text="Настройка фильтров"))
        tb.add_widget(filters_tab)

        # Вкладка "Словарь"
        dictionary_tab = TabbedPanelItem(
            text="Словарь", font_size="12sp", size_hint=(None, None), width=50, height=22
        )

        # Основной layout для вкладки "Словарь"
        main_layout = BoxLayout(orientation="vertical", spacing=5, padding=5)

        # GridLayout для верхних элементов (кнопки и таблица)
        top_layout = GridLayout(cols=2, spacing=10, padding=5, size_hint=(1, 0.5))

        # GridLayout для нижних текстовых полей
        bottom_layout = GridLayout(cols=2, spacing=10, padding=5, size_hint=(1, 0.5))

        # TextInput в левой верхней ячейке
        self.text_input_1 = BoxLayout(orientation='vertical', size_hint=(1, 1))

        # Создаем кнопки
        button_dict_1 = IconButtonWithTooltip(
            icon="file-document-outline",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#DCDCDC",
            icon_size="10dp",
            tooltip_text="Создать новый словарь",
        )
        button_dict_1.bind(on_release=self.show_confirmation_dialog_dict)
        button_dict_2 = IconButtonWithTooltip(
            icon="folder-file",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#FFFACD",
            icon_size="10dp",
            tooltip_text="Создать новую папку",
        )
        button_dict_3 = IconButtonWithTooltip(
            icon="file-refresh-outline",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#98FB98",
            icon_size="10dp",
            tooltip_text="Добавить папку как новый фильтр",
        )
        button_dict_4 = IconButtonWithTooltip(
            icon="reply-all",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#00FA9A",
            icon_size="10dp",
            tooltip_text="Добавить все папки как новые фильтры",
        )
        button_dict_5 = IconButtonWithTooltip(
            icon="window-close",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#e33d3d",
            icon_size="10dp",
            tooltip_text="Удалить выделенное",
        )
        # Горизонтальный layout для кнопок
        buttons_layout = BoxLayout(
            orientation="horizontal",
            spacing=5,
            size_hint=(1, None),
            height=40,  # Высота для кнопок
        )

        # Добавляем кнопки в горизонтальный layout
        buttons_layout.add_widget(button_dict_1)
        buttons_layout.add_widget(button_dict_2)
        buttons_layout.add_widget(button_dict_3)
        buttons_layout.add_widget(button_dict_4)
        buttons_layout.add_widget(button_dict_5)

        # Вертикальный layout для кнопок и текстового поля
        left_top_layout = BoxLayout(
            orientation="vertical",
            spacing=5,
            size_hint=(0.4, 1),
        )

        # Добавляем кнопки и текстовое поле в вертикальный layout
        left_top_layout.add_widget(buttons_layout)
        left_top_layout.add_widget(self.text_input_1)

        # Вставляем MDDataTable в правую верхнюю ячейку
        self.data_table = MDDataTable(
            size_hint=(1, 1),
            check=True,
            column_data=[
                ("Лексема", dp(50)),
                ("Частота", dp(30)),
                ("Длина", dp(30)),
            ],
            row_data=[],
            use_pagination=True,  # Включаем пагинацию
        )
        # Кнопка над таблицей
        table_button = IconButtonWithTooltip(
            icon="folder-file",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#FFDEAD",
            icon_size="10dp",
            tooltip_text="Создать именованные папки из выделенного",
            size_hint=(None, None),
        )

        # Создаем контейнер для таблицы
        right_top_layout = BoxLayout(orientation="vertical")
        right_top_layout.add_widget(table_button)
        right_top_layout.add_widget(self.data_table)

        # Добавляем элементы в верхний layout
        top_layout.add_widget(left_top_layout)
        top_layout.add_widget(right_top_layout)

        # Горизонтальный BoxLayout для кнопок между уровнями
        middle_buttons_layout = BoxLayout(
            orientation="horizontal",
            spacing=10,  # Пробел между кнопками
            size_hint=(1, None),  # Растянуть по ширине
            height=40,  # Высота кнопок
            pos_hint={"center_x": 0.8},
        )
        # Кнопки между уровнями
        middle_button_1 = IconButtonWithTooltip(
            icon="arrow-down",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#32CD32",
            icon_size="10dp",
            tooltip_text="Перенести выделенное",
            size_hint=(None, None),
        )
        middle_button_2 = IconButtonWithTooltip(
            icon="arrow-up",
            icon_color=(0.5, 0.5, 1, 1),
            md_bg_color="#32CD32",
            icon_size="10dp",
            tooltip_text="Перенести выделенное",
            size_hint=(None, None),
        )

        # Добавляем кнопки в горизонтальный layout
        middle_buttons_layout.add_widget(middle_button_1)
        middle_buttons_layout.add_widget(middle_button_2)

        # TextInput в нижнем левом углу
        self.text_input_3 = BoxLayout(orientation='vertical', size_hint=(0.4, 1))

        # TextInput в нижнем правом углу
        text_input_4 = TextInput(multiline=True, size_hint=(1, 1))

        # Добавляем элементы в нижний layout
        bottom_layout.add_widget(self.text_input_3)
        bottom_layout.add_widget(text_input_4)

        # Добавляем верхний layout, кнопку и нижний layout в основной layout
        main_layout.add_widget(top_layout)
        main_layout.add_widget(middle_buttons_layout)
        main_layout.add_widget(bottom_layout)

        # Добавление основного layout в вкладку "Словарь"
        dictionary_tab.add_widget(main_layout)
        tb.add_widget(dictionary_tab)

        # Вкладка "Факторный анализ"
        filters_tab = TabbedPanelItem(
            text="Факторный анализ", font_size="11sp", size_hint=(None, None), width=50, height=22
        )
        filters_tab.add_widget(Label(text="Факторный анализ"))
        tb.add_widget(filters_tab)

        return tb





    ############################ Создать новый словарь ################################
    def show_confirmation_dialog_dict(self, instance):
        """
        Отображает предупреждающее окно перед созданием нового словаря.
        """
        if not self.dialog:
            self.dialog = MDDialog(
                title="Внимание!",
                text="При создании нового словаря все текущие данные будут утеряны! Продолжить?",
                buttons=[
                    MDRectangleFlatButton(
                        text="Отмена",
                        on_release=self.cancel_action_dict  # Обработчик отмены
                    ),
                    MDRectangleFlatButton(
                        text="Да",
                        on_release=self.confirm_action_dict  # Обработчик подтверждения
                    ),
                ],
            )
        self.dialog.open()  # Открываем диалог

    def cancel_action_dict(self, instance):
        """
        Обработчик кнопки "Отмена".
        """
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None  # Обнуляем ссылку

    def confirm_action_dict(self, instance):
        """
        Обработчик кнопки "ОК".
        """
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None  # Обнуляем ссылку
        self.on_create_dictionary(None)

    def on_create_dictionary(self, instance):
        """
        Обработчик нажатия на кнопку "Создать новый словарь".
        """
        # Словарь для подсчета частоты слов
        word_frequency = {}

        # Проход по всем строкам в таблице фрагментов (self.texts)
        for fragment in self.texts:
            if isinstance(fragment, tuple):
                fragment_text = fragment[1]  # Извлекаем текст из кортежа (например, 2-й элемент)
            else:
                fragment_text = fragment  # Если это уже строка, используем как есть

            words = fragment_text.split()  # Разделяем текст на слова

            for word in words:
                cleaned_word = re.sub(r'[^\w\-]', '', word).lower()  # Очистка слова
                if cleaned_word:  # Проверяем, что слово не пустое
                    word_frequency[cleaned_word] = word_frequency.get(cleaned_word, 0) + 1
                    # Добавляем слово в список базового словаря, если оно не пустое
                    if cleaned_word not in self.base_dict_words:
                        self.base_dict_words.append(cleaned_word)

        self.logger.debug(f"Список слов в кнопке 'Базовый словарь: '{self.base_dict_words}")

        # Формируем данные для таблицы, сортируем по частоте в убывающем порядке
        row_data = [
            (word, str(freq), str(len(word)))
            for word, freq in sorted(word_frequency.items(), key=lambda x: x[1], reverse=True)  # Сортировка по частоте
        ]

        # Обновляем данные в MDDataTable
        self.update_dictionary_table(row_data)

        # Добавление кнопок в левую область верхнего TextInput
        self.create_left_buttons_top(len(word_frequency))

        # Добавление кнопок в левую область нижнего TextInput
        self.create_left_buttons_bottom(len(word_frequency))

    def create_left_buttons_top(self, word_count):
        """
        Создает кнопки "Базовый словарь" и "Корзина" в левую область с активным состоянием.
        """
        # Очищаем левый контейнер
        self.text_input_1.clear_widgets()

        # Создаём ScrollView для прокрутки
        scroll_view = ScrollView(size_hint=(1, 1))

        # Контейнер для кнопок внутри ScrollView
        button_container = BoxLayout(orientation='vertical', size_hint_y=None)
        button_container.bind(minimum_height=button_container.setter('height'))  # Динамическая высота

        # Создание кнопки "Базовый словарь"
        self.base_dict_button = MDRectangleFlatIconButton(
            text=f"!!! Базовый словарь !!! ({word_count})",
            size_hint=(1, None),
            icon="book-alphabet",
            height=30,
            text_color="white",
            line_color="yellow",
            icon_color="yellow",
            on_press=self.set_active_button,  # Обработчик для активации
        )

        # Создание кнопки "Корзина"
        self.trash_button = MDRectangleFlatIconButton(
            text="Корзина",
            size_hint=(1, None),
            icon="trash-can-outline",
            height=30,
            text_color="white",
            line_color="green",
            icon_color="green",
            on_press=self.set_active_button,  # Обработчик для активации
        )

        # Создание текстового поля
        text_input_1 = TextInput(multiline=True, size_hint=(1, 1), height=150)

        # Добавляем элементы в контейнер кнопок
        button_container.add_widget(self.base_dict_button)
        button_container.add_widget(self.trash_button)
        button_container.add_widget(text_input_1)

        # Добавляем контейнер кнопок в ScrollView
        scroll_view.add_widget(button_container)

        # Очищаем основной контейнер и добавляем в него ScrollView
        self.text_input_1.add_widget(scroll_view)

    def on_base_dict_button_press_top(self, instance):
        """
        Обработчик нажатия на кнопку "Базовый словарь" в верхнем поле слева.
        """
        print("Кнопка 'Базовый словарь' нажата. Добавьте сюда функционал.")

    def on_trash_button_press_top(self, instance):
        """
        Обработчик нажатия на кнопку "Корзина" в верхнем поле слева.
        """
        print("Кнопка 'Корзина' нажата. Добавьте сюда функционал.")

    def create_left_buttons_bottom(self, word_count):
        """
        Создает кнопки "Базовый словарь" и "Корзина" в левую область внизу с активным состоянием.
        """
        # Очищаем левый контейнер
        self.text_input_3.clear_widgets()

        # Создаём ScrollView для прокрутки
        scroll_view = ScrollView(size_hint=(1, 1))

        # Контейнер для кнопок внутри ScrollView
        button_container = BoxLayout(orientation='vertical', size_hint_y=None)
        button_container.bind(minimum_height=button_container.setter('height'))  # Динамическая высота

        # Создание кнопки "Базовый словарь"
        self.base_dict_button_bottom = MDRectangleFlatIconButton(
            text=f"!!! Базовый словарь !!! ({word_count})",
            size_hint=(1, None),
            icon="book-alphabet",
            height=30,
            text_color="white",
            line_color="yellow",
            icon_color="yellow",
            on_press=self.set_active_button,  # Обработчик для активации
        )

        # Создание кнопки "Корзина"
        self.trash_button_bottom = MDRectangleFlatIconButton(
            text="Корзина",
            size_hint=(1, None),
            icon="trash-can-outline",
            height=30,
            text_color="white",
            line_color="green",
            icon_color="green",
            on_press=self.set_active_button,  # Обработчик для активации
        )

        # Создание текстового поля
        text_input_3 = TextInput(multiline=True, size_hint=(1, 1), height=150)

        # Добавляем элементы в контейнер кнопок
        button_container.add_widget(text_input_3)
        button_container.add_widget(self.base_dict_button_bottom)
        button_container.add_widget(self.trash_button_bottom)

        # Добавляем контейнер кнопок в ScrollView
        scroll_view.add_widget(button_container)

        # Очищаем основной контейнер и добавляем в него ScrollView
        self.text_input_3.add_widget(scroll_view)

    def on_base_dict_button_press_bottom(self, instance):
        """
        Обработчик нажатия на кнопку "Базовый словарь" внизу.
        """
        print("Кнопка 'Базовый словарь' внизу нажата.")

    def on_trash_button_press_bottom(self, instance):
        """
        Обработчик нажатия на кнопку "Корзина" внизу.
        """
        print("Кнопка 'Корзина' внизу нажата.")

    def update_dictionary_table(self, row_data):
        """
        Обновляет данные в таблице словаря.
        """
        # Очищаем таблицу
        self.data_table.row_data = []  # Сброс текущих данных

        # Устанавливаем новые данные
        self.data_table.row_data = row_data

    def set_active_button(self, instance):
        """
        Устанавливает активное состояние для нажатой кнопки.
        """
        # Сбрасываем состояние всех кнопок
        for button in [self.base_dict_button, self.trash_button, self.base_dict_button_bottom,
                       self.trash_button_bottom]:
            if button in [self.base_dict_button, self.base_dict_button_bottom]:
                # Для кнопок базового словаря
                button.text_color = "white"
                button.line_color = "yellow"
                button.icon_color = "yellow"
            elif button in [self.trash_button, self.trash_button_bottom]:
                # Для кнопок корзины
                button.text_color = "white"
                button.line_color = "green"
                button.icon_color = "green"

        # Устанавливаем активное состояние для текущей кнопки
        instance.text_color = "blue"
        instance.line_color = "blue"
        instance.icon_color = "blue"
    ###################################################################################

















    ############################ Обработка ################################
    def show_processing_dialog(self, *args):
        # Создаем диалоговое окно выбора действия
        if not self.dialog:  # Проверяем, что диалог не открыт
            self.dialog = MDDialog(
                title="Выберите действие:",
                type="simple",
                buttons=[
                    MDRectangleFlatButton(
                        text="Разбить на фрагменты",
                        on_release=self.show_fragmentation_settings,  # Обработчик для кнопки
                    ),
                    MDRectangleFlatButton(
                        text="Применить фильтры",
                        on_release=self.apply_filters,
                    ),
                ],
            )
        self.dialog.open()

    def show_fragmentation_settings(self, *args):
        print("Кнопка 'Разбить на фрагменты' нажата")

        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        def on_checkbox_active(instance, value):
            print(f"{instance.id} активирован" if value else f"{instance.id} деактивирован")

        # Сохранение ссылок на чекбоксы
        self.checkbox_size = MDCheckbox(
            size_hint=(None, None),
            size=("48dp", "48dp"),
            pos_hint={"center_y": 0.5},
        )
        self.checkbox_size.id = "checkbox_size"
        self.checkbox_size.bind(active=on_checkbox_active)

        self.checkbox_row = MDCheckbox(
            size_hint=(None, None),
            size=("48dp", "48dp"),
            pos_hint={"center_y": 0.5},
        )
        self.checkbox_row.id = "checkbox_row"
        self.checkbox_row.bind(active=on_checkbox_active)

        # Создаем интерфейс диалога вручную
        content = BoxLayout(
            orientation="vertical",
            spacing="20dp",
            padding="20dp",
            size_hint_y=None,
            height="350dp"
        )

        row_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="30dp", spacing="10dp")
        row_layout.add_widget(MDLabel(text="Разбить по строке", size_hint=(1, None), height="30dp"))
        row_layout.add_widget(self.checkbox_row)

        size_layout = BoxLayout(orientation="horizontal", size_hint_y=None, height="70dp", spacing="10dp")
        size_layout.add_widget(MDLabel(text="Разбить по размеру", size_hint=(1, None), height="70dp"))
        size_layout.add_widget(self.checkbox_size)

        # Поля ввода
        input_layout = BoxLayout(orientation="vertical", spacing="10dp", size_hint_y=None, padding="10dp")
        target_input = MDTextField(hint_text="Пример: 50", size_hint=(1, None), height="50dp")
        self.target_input = target_input
        tolerance_input = MDTextField(hint_text="Пример: 20", size_hint=(1, None), height="50dp")
        self.tolerance_input = tolerance_input

        row_target_layout = BoxLayout(orientation="horizontal", spacing="10dp", size_hint_y=None, height="50dp")
        row_target_layout.add_widget(MDLabel(text="Цель", size_hint=(None, None), size=("50dp", "50dp")))
        row_target_layout.add_widget(target_input)

        row_tolerance_layout = BoxLayout(orientation="horizontal", spacing="10dp", size_hint_y=None, height="50dp")
        row_tolerance_layout.add_widget(MDLabel(text="+-", size_hint=(None, None), size=("50dp", "50dp")))
        row_tolerance_layout.add_widget(tolerance_input)

        input_layout.add_widget(row_target_layout)
        input_layout.add_widget(row_tolerance_layout)

        button_box = BoxLayout(size_hint_y=None, height="50dp", spacing=10)
        ok_button = MDRectangleFlatButton(text="OK", on_release=self.confirm_fragmentation)
        cancel_button = MDRectangleFlatButton(text="Отменить", on_release=self.cancel_dialog)
        button_box.add_widget(ok_button)
        button_box.add_widget(cancel_button)

        content.add_widget(row_layout)
        content.add_widget(size_layout)
        content.add_widget(input_layout)
        content.add_widget(button_box)

        self.dialog = MDDialog(
            title="Настройка фрагментатора",
            type="custom",
            content_cls=content,
        )
        self.dialog.open()

    def apply_filters(self, *args):
        # Логика применения фильтров
        print("Применение фильтров")
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None  # Обнуляем ссылку на диалог

    def show_preloader(self):
        """Отображает прелоадер"""
        self.preloader = Popup(
            title="Выполняется обработка...",
            content=Label(text="Подождите, идет обработка фрагментов..."),
            size_hint=(0.5, 0.5),
            auto_dismiss=False,
        )
        self.preloader.open()

    def hide_preloader(self):
        """Скрывает прелоадер"""
        if hasattr(self, 'preloader') and self.preloader:
            self.preloader.dismiss()
            self.preloader = None

    def confirm_fragmentation(self, *args):
        print("Фрагментация настроена")

        # Проверка чекбоксов
        size_split = self.checkbox_size.active
        row_split = self.checkbox_row.active

        # Проверка значений в полях ввода
        target = self.target_input.text
        tolerance = self.tolerance_input.text

        if not target.isdigit() or not tolerance.isdigit():
            print("Некорректные значения в полях ввода")
            return

        target = int(target)
        tolerance = int(tolerance)

        # Получаем текст из text_area или из загруженных файлов
        selected_texts = self.get_text_from_area_or_fragments()
        print(f"Выбранные тексты: {selected_texts}")

        if not selected_texts:
            print("Не выбран текст для разбиения")
            return

        # Отображаем прелоадер
        self.show_preloader()

        # Запускаем вычисления в потоке
        Thread(
            target=self._fragment_texts_in_thread,
            args=(selected_texts, size_split, row_split, target, tolerance),
            daemon=True
        ).start()
        self.dialog = None  # Обнуляем ссылку на диалог

    def split_by_size(self, text_iterable, target, tolerance):
        if not text_iterable:
            return
        buffer = []
        for word in text_iterable:
            buffer.append(word)
            if len(buffer) >= target:
                yield " ".join(buffer)
                buffer = []
        if buffer and len(buffer) >= tolerance:
            yield " ".join(buffer)

    def process_large_texts(self, selected_texts, target, tolerance, max_workers=1500):
        """
        Параллельная фрагментация больших текстов.
        :param selected_texts: Список текстов для фрагментации.
        :param target: Желаемое количество слов в одном фрагменте.
        :param tolerance: Минимальное количество слов для включения фрагмента в результат.
        :param max_workers: Количество потоков для параллельной обработки.
        :return: Список фрагментированных текстов.
        """

        def fragment_text(text):
            # Проверяем длину текста и ограничиваем обработку
            if len(text.split()) > target * 10:  # Примерное ограничение
                print("Обрабатывается большой текст...")
            return list(self.split_by_size(text.split(), target, tolerance))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(fragment_text, selected_texts)
        return list(chain.from_iterable(results))  # Сразу объединяем фрагменты

    def _fragment_texts_in_thread(self, selected_texts, size_split, row_split, target, tolerance):
        """
        Выполняет фрагментацию текста в отдельном потоке и обновляет интерфейс.
        """
        from itertools import chain

        fragmented_texts = []
        if size_split:
            fragmented_texts = self.process_large_texts(selected_texts, target, tolerance)
        elif row_split:
            fragmented_texts = list(chain.from_iterable(text.splitlines() for text in selected_texts))

        # Переход обратно в основной поток для обновления интерфейса
        Clock.schedule_once(lambda dt: self._update_ui_after_fragmentation(fragmented_texts))

    def _update_ui_after_fragmentation(self, fragmented_texts):
        """
        Обновляет интерфейс после фрагментации текста.
        """
        # Скрываем прелоадер
        self.hide_preloader()

        # Подсчитываем количество фрагментов
        num_fragments = len(fragmented_texts)

        # Показать всплывающее окно с информацией
        info_popup = Popup(
            title="Обработка завершена",
            content=Label(text=f"Фрагментация завершена.\nКоличество фрагментов: {num_fragments}"),
            size_hint=(0.5, 0.5),
            auto_dismiss=True
        )
        info_popup.open()

        # Здесь можно обновить интерфейс с результатами
        self.update_table_and_text_area(fragmented_texts)

    def get_text_from_area_or_fragments(self):
        if self.text_area.text.strip() != 'Нет текста':  # Дополнительная проверка
            print(f"Текст в text_area: '{self.text_area.text}'")
            return [self.text_area.text]
        else:
            if self.texts:
                selected_texts = [text for _, text in self.texts]
                print(f"Тексты из загруженных файлов: {selected_texts}")
                return selected_texts
            print("Нет текста для разбиения.")
            return []

    def get_selected_texts(self):
        selected_texts = []
        for row in self.table_layout.children:  # Проходим по всем виджетам в GridLayout
            if isinstance(row, CheckBox) and row.active:
                parent = row.parent
                if parent:
                    for child in parent.children:
                        if isinstance(child, Label):
                            text = child.text.strip()  # Добавляем текст метки
                            if text:  # Проверяем, что текст не пустой
                                print(f"Добавлен текст: '{text}'")
                                selected_texts.append(text)
        return selected_texts

    def update_table_and_text_area(self, fragmented_texts):
        """
        Обновляет таблицу и текстовую область с новыми фрагментами.
        Структурирует таблицу с заголовками "##", "Фрагмент", "Слов", "Выбрать".
        """
        # Очищаем таблицу и текстовую область
        self.table_layout.clear_widgets()  # Очищаем все виджеты в таблице
        self.text_area.clear_widgets()  # Очищаем текстовую область

        # Создание ScrollView для таблицы
        scroll_view = ScrollView(size_hint=(1, 1))  # ScrollView на всю ширину и высоту
        scroll_content = GridLayout(cols=4, size_hint_y=None)  # Сеточный лейаут для таблицы
        scroll_content.bind(minimum_height=scroll_content.setter('height'))  # Автоматическая настройка высоты контента

        # Добавляем заголовки в таблицу слева
        headers = ["##", "Фрагмент", "Слов", "Выбрать"]
        for header in headers:
            scroll_content.add_widget(BorderedCell(Label(text=header, size_hint_y=None, height=20, font_size="12sp")))

        # Перебираем фрагментированные тексты
        for idx, text in enumerate(fragmented_texts, start=1):
            word_count = len(text.split())

            # Создание и привязка кнопки с числовой нумерацией
            button = Button(text=str(idx), size_hint_y=None, height=20)
            button.bind(on_press=lambda btn, idx=idx: self.on_fragment_button_press(idx, fragmented_texts))
            scroll_content.add_widget(BorderedCell(button))

            # Создание и добавление метки с фрагментом
            scroll_content.add_widget(BorderedCell(Label(text='txt', size_hint_y=None, height=20)))

            # Добавление метки с количеством слов
            scroll_content.add_widget(BorderedCell(Label(text=str(word_count), size_hint_y=None, height=20)))

            # Создание чекбокса с уникальным идентификатором для фрагмента
            check_box = CheckBox(size_hint_y=None, height=20)
            check_box.fragment_id = idx  # Привязываем индекс фрагмента как уникальный идентификатор
            scroll_content.add_widget(BorderedCell(check_box))

            # Создание метки для текстовой области
            self.text_area.add_widget(Label(text=text))

        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)

    def on_fragment_button_press(self, idx, fragmented_texts):
        """
        Обработчик нажатия на кнопку фрагмента. Обновляет текстовое поле.
        """
        # Получаем текст фрагмента по индексу и обновляем текстовую область
        selected_text = fragmented_texts[idx - 1]  # Индексация начинается с 1
        self.text_area.text = selected_text  # Устанавливаем текст непосредственно в поле

    def cancel_dialog(self, *args):
        # Отмена диалога
        print("Диалог отменен")
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None  # Обнуляем ссылку на диалог

    #############################################################################


    ############################ Загрузка файлов ################################
    def open_file_dialog(self, instance):
        """
        Открывает диалог выбора файлов с поддержкой множественного выбора.
        """
        file_chooser = FileChooserIconView(filters=["*.txt"], multiselect=True)
        popup_content = BoxLayout(orientation="vertical")
        popup_content.add_widget(file_chooser)

        # Создаем кнопку для подтверждения выбора файлов
        confirm_button = Button(text="Загрузить файлы", size_hint_y=None, height=40)
        confirm_button.bind(on_release=lambda btn: self.load_files(file_chooser.selection, popup))

        popup_content.add_widget(confirm_button)

        # Создаем попап и отображаем его
        popup = Popup(title="Выберите файлы", content=popup_content, size_hint=(0.9, 0.9))
        popup.open()

    def load_files(self, file_paths, popup):
        """
        Загружает несколько текстовых файлов и обновляет прогрессбар по мере загрузки.
        """
        if popup:  # Проверка на None перед вызовом dismiss
            popup.dismiss()  # Закрываем попап
        self.texts = []  # Сброс списка текстов
        self.table_layout.clear_widgets()  # Очищаем таблицу

        # Создание ScrollView для таблицы
        scroll_view = ScrollView(size_hint=(1, 1))  # ScrollView на всю ширину и высоту
        scroll_content = GridLayout(cols=4, size_hint_y=None)  # Сеточный лейаут для таблицы
        scroll_content.bind(minimum_height=scroll_content.setter('height'))  # Автоматическая настройка высоты контента

        # Заголовки таблицы
        headers = ["##", "Фрагмент", "Слов", "Выбрать"]
        for header in headers:
            scroll_content.add_widget(BorderedCell(Label(text=header, size_hint_y=None, height=20, font_size="12sp")))

        # Логируем начало загрузки
        self.logger.info("Начинаем загрузку файлов.")

        # Инициализируем прогрессбар
        total_files = len(file_paths)
        self.progress_bar.max = total_files
        self.progress_bar.value = 0

        # Добавляем строки таблицы
        for i, file_path in enumerate(file_paths, start=1):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read().strip()  # Убираем лишние пробелы
                    self.texts.append((file_path, text))  # Добавляем текст в список

                    # Логируем успешную загрузку текста
                    self.logger.debug(f"Файл загружен: {file_path}, текст длиной {len(text)} символов.")

                    words_count = len(text.split())

                    # Генерация короткого имени файла для отображения
                    file_name = file_path.split("/")[-1]  # Получаем только имя файла
                    if len(file_name) > 10:
                        fragment = f"{file_name[:4]}..{file_name[-4:]}"  # Сокращённое название
                    else:
                        fragment = file_name  # Если имя короткое, используем его целиком

                    # Используем partial для передачи правильного индекса в on_release
                    button = Button(text=str(i), size_hint_y=None, height=20)
                    button.bind(on_release=partial(self.display_text, i - 1))  # Передаем индекс

                    # Чекбокс для выбора
                    checkbox = CheckBox(size_hint_y=None, height=20)
                    checkbox.fragment_id = file_path  # Присваиваем уникальный идентификатор для файла

                    # Добавляем элементы в таблицу
                    scroll_content.add_widget(BorderedCell(button))
                    scroll_content.add_widget(BorderedCell(Label(text=fragment, size_hint_y=None, height=20)))
                    scroll_content.add_widget(BorderedCell(Label(text=str(words_count), size_hint_y=None, height=20)))
                    scroll_content.add_widget(BorderedCell(checkbox))

            except Exception as e:
                # Логируем ошибку при загрузке файла
                self.logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
                self.text_area.text = f"Ошибка при загрузке файла {file_path}: {e}"

            # Обновляем прогрессбар после обработки каждого файла
            self.progress_bar.value += 1

        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)

        # Логируем состояние словаря self.texts после загрузки
        self.logger.debug(f"Состояние self.texts после загрузки: {self.texts}")

    def display_text(self, index, instance=None):
        """
        Отображает текст выбранного файла.
        """
        file_path, text = self.texts[index]
        # Отображение текста в правом окне
        self.text_area.text = f"{text}"

    #############################################################################

    ############################ Выделение чекбоксов ################################
    def select_all_checkboxes(self, instance):
        """
        Отмечает все чекбоксы в таблице.
        """
        # Перебираем элементы в table_layout
        for child in self.table_layout.children:
            # Если это ScrollView, ищем GridLayout внутри него
            if isinstance(child, ScrollView):
                for scroll_content_child in child.children:
                    if isinstance(scroll_content_child, GridLayout):  # Находим GridLayout внутри ScrollView
                        for checkbox in scroll_content_child.children:
                            if isinstance(checkbox, CheckBox):
                                checkbox.active = True  # Отмечаем чекбокс
            # Если это GridLayout, перебираем его чекбоксы
            elif isinstance(child, GridLayout):
                for checkbox in child.children:
                    if isinstance(checkbox, CheckBox):
                        checkbox.active = True  # Отмечаем чекбокс

    def disable_all_checkboxes(self, instance):
        """
        Убирает отметки всех чекбоксов в таблице.
        """
        # Перебираем элементы в table_layout
        for child in self.table_layout.children:
            # Если это ScrollView, ищем GridLayout внутри него
            if isinstance(child, ScrollView):
                for scroll_content_child in child.children:
                    if isinstance(scroll_content_child, GridLayout):  # Находим GridLayout внутри ScrollView
                        for checkbox in scroll_content_child.children:
                            if isinstance(checkbox, CheckBox):
                                checkbox.active = False  # Снимаем отметку с чекбокса
            # Если это GridLayout, перебираем его чекбоксы
            elif isinstance(child, GridLayout):
                for checkbox in child.children:
                    if isinstance(checkbox, CheckBox):
                        checkbox.active = False  # Снимаем отметку с чекбокса

    #############################################################################

    ############################ Разделение фрагмента на 2 части по местоположению курсора ################################
    def split_text(self, instance):
        print("split_text called")
        cursor_position = self.text_area.cursor_index()  # Получаем текущую позицию курсора
        text = self.text_area.text.strip()

        if not text:
            print("Text is empty, aborting split")
            return

        # Проверяем, является ли это фрагментом или загруженным файлом
        original_key = None
        is_file = False
        for key, fragment_text in self.fragments.items():
            if fragment_text == text:
                original_key = key
                break

        if original_key is None:
            # Проверяем среди файлов
            for file_name, file_text in self.files.items():  # `self.files` — это словарь с загруженными файлами
                if file_text == text:
                    original_key = file_name  # Устанавливаем как имя файла
                    is_file = True
                    break

        if original_key is None:
            # Генерируем новый ключ и добавляем текст
            original_key = f"frag.{len(self.fragments) + 1}"
            self.fragments[original_key] = text
            print(f"Added original text to fragments with key: {original_key}")

        # Разделение текста
        first_part = text[:cursor_position].strip()
        second_part = text[cursor_position:].strip()

        print("First part:", first_part)
        print("Second part:", second_part)

        if not first_part or not second_part:
            print("One of the parts is empty, aborting split")
            return

        # Обновление для фрагмента
        if not is_file:
            # Удаляем исходный фрагмент из словаря
            del self.fragments[original_key]

            # Обновляем оригинальный ключ с первой частью
            self.fragments[original_key] = first_part

            # Создаем ключ для новой части
            new_key = f"{original_key}.1"

            # Добавляем новую часть
            new_fragments = {
                new_key: second_part,
            }
            self.fragments.update(new_fragments)
        else:
            # Для файлов: обновляем содержимое файла
            self.files[original_key] = first_part
            new_key = f"{original_key}.1"
            self.files[new_key] = second_part

        # Обновляем текст в text_area (оставляем первую часть)
        self.text_area.text = first_part

        print("Updated fragments/files:", self.fragments, self.files)

        # Обновляем таблицу: удаляем оригинальный элемент и добавляем обе части
        if is_file:
            self.update_table(removed_key=original_key, new_fragments={original_key: first_part, new_key: second_part})
        else:
            self.update_table(removed_key=original_key, new_fragments={original_key: first_part, new_key: second_part})

    def update_table(self, removed_key=None, new_fragments=None):
        """
        Обновляет таблицу: удаляет строку с `removed_key` и добавляет строки из `new_fragments`.
        """
        print("Updating table...")
        print(f"Removed key: {removed_key}")
        print(f"New fragments: {new_fragments}")

        if removed_key:
            # Удаляем строку, связанную с removed_key
            widgets_to_remove = []
            for i, child in enumerate(self.table_layout.children[:]):
                widget_text = getattr(child, 'text', '').strip()
                if widget_text == removed_key.strip():
                    # Удаляем строку (4 виджета: кнопка, ключ, счетчик слов, чекбокс)
                    widgets_to_remove.extend(self.table_layout.children[i:i + 4])
                    break

            if widgets_to_remove:
                for widget in widgets_to_remove:
                    print(f"Removing widget: {widget} | Text: {getattr(widget, 'text', 'No text')}")
                    self.table_layout.remove_widget(widget)
            else:
                print(f"Key {removed_key} not found in table_layout!")

        if new_fragments:
            # Добавляем новые строки для фрагментов или файлов
            for key, fragment_text in new_fragments.items():
                word_count = len(fragment_text.split())

                # Проверяем, это фрагмент или файл
                if key.startswith("frag"):
                    # Это фрагмент текста
                    button = Button(text=str(len(self.fragments)), size_hint_y=None, height=20)
                    button.bind(
                        on_press=lambda instance, text=fragment_text, key=key: self.view_fragment(text, instance, key)
                    )
                else:
                    # Это файл
                    button = Button(text=key, size_hint_y=None, height=20)
                    button.bind(
                        on_press=lambda instance, text=fragment_text, key=key: self.view_fragment(text, instance, key)
                    )

                # Добавляем новые виджеты в таблицу
                self.table_layout.add_widget(button)
                self.table_layout.add_widget(Label(text=key, size_hint_y=None, height=20))
                self.table_layout.add_widget(Label(text=str(word_count), size_hint_y=None, height=20))
                self.table_layout.add_widget(CheckBox(size_hint_y=None, height=20))

                print(f"Added fragment/file: {key} with word count {word_count}")

    def view_fragment(self, fragment_text, instance=None, fragment_key=None):
        """
        Обработчик для отображения содержимого фрагмента текста.
        Этот метод будет отображать фрагмент в text_area.
        """
        # Отображаем фрагмент в text_area
        self.text_area.text = fragment_text

        # Если это тот фрагмент, который мы разделили, удаляем его
        if fragment_key == self.current_fragment_to_remove:
            del self.fragments[fragment_key]

        # Обновляем таблицу, чтобы отобразить изменения
        self.update_table()

    #############################################################################

    ############################ Удаление фрагментов по выделенному чекбоксу ################################
    def delete_selected_fragments(self, instance):
        """
        Удаляет фрагменты с выделенными чекбоксами.
        """
        # Получаем список всех чекбоксов в таблице
        checkboxes = [widget for widget in self.table_layout.walk() if isinstance(widget, CheckBox)]

        # Перебираем все чекбоксы и проверяем, если они отмечены
        for checkbox in checkboxes:
            if checkbox.active:  # Если чекбокс выбран
                file_path = checkbox.fragment_id  # Получаем уникальный идентификатор файла (путь)

                # Удаляем фрагмент из списка self.texts
                self.texts = [text for text in self.texts if text[0] != file_path]

                # Удаляем строку с таблицы (кнопки и чекбокс, связанные с фрагментом)
                for widget in self.table_layout.children:
                    if isinstance(widget, GridLayout):
                        for child in widget.children:
                            if isinstance(child, CheckBox) and child.fragment_id == file_path:
                                widget.remove_widget(child)
                            elif isinstance(child, Button) and child.text == str(self.texts.index((file_path, _)) + 1):
                                widget.remove_widget(child)
                            elif isinstance(child, Label) and (
                                    child.text == file_path.split("/")[-1] or child.text == str(
                                    len(file_path.split()))):
                                widget.remove_widget(child)

                # Логируем удаление фрагмента
                self.logger.info(f"Фрагмент {file_path} удален.")

        # Обновляем интерфейс (можно добавить очистку и перерисовку элементов)
        self.table_layout.clear_widgets()
        self.load_files([file[0] for file in self.texts], popup=None)  # Перезагружаем таблицу без удалённых файлов

    def update_table_after_deletion(self):
        """Обновляет отображение таблицы после удаления фрагментов."""
        self.table_layout.clear_widgets()  # Полностью очищаем таблицу

        # Создаем новую таблицу
        scroll_view = ScrollView(size_hint=(1, 1))  # ScrollView на всю ширину и высоту
        scroll_content = GridLayout(cols=4, size_hint_y=None)  # Сеточный лейаут для таблицы
        scroll_content.bind(minimum_height=scroll_content.setter('height'))  # Автоматическая настройка высоты контента

        # Заголовки таблицы
        headers = ["##", "Фрагмент", "Слов", "Выбрать"]
        for header in headers:
            scroll_content.add_widget(BorderedCell(Label(text=header, size_hint_y=None, height=20, font_size="12sp")))

        # Добавляем строки таблицы
        for i, (fragment_id, fragment) in enumerate(self.fragments.items()):
            words_count = len(fragment.split())

            # Короткое имя файла для отображения
            file_name = fragment_id.split("/")[-1]
            if len(file_name) > 10:
                display_name = f"{file_name[:4]}..{file_name[-4:]}"
            else:
                display_name = file_name

            # Кнопка с индексом
            button = Button(text=str(i), size_hint_y=None, height=20)
            button.bind(on_release=partial(self.display_text, i))

            # Чекбокс для выбора
            checkbox = CheckBox(size_hint_y=None, height=20)
            checkbox.fragment_id = fragment_id  # Идентификатор фрагмента

            # Добавляем виджеты в таблицу
            scroll_content.add_widget(BorderedCell(button))
            scroll_content.add_widget(BorderedCell(Label(text=display_name, size_hint_y=None, height=20)))
            scroll_content.add_widget(BorderedCell(Label(text=str(words_count), size_hint_y=None, height=20)))
            scroll_content.add_widget(BorderedCell(checkbox))

        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)
    #############################################################################


if __name__ == "__main__":
    DataLexApp().run()
