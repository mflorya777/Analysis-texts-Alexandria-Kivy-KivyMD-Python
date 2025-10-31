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
import os

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
        self.current_text_index = None  # Индекс выбранного текста из self.texts
        self.current_selected_button = None  # Текущая выбранная кнопка для визуального выделения

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

    def shorten_filename(self, filename, max_length=15):
        """
        Сокращает длинное имя файла.
        Например: 'Экология.txt' остаётся как есть, 'ДлинноеИмяФайла.txt' -> 'Дли...txt'
        """
        if len(filename) <= max_length:
            return filename
        
        # Разделяем имя и расширение
        name, ext = os.path.splitext(filename)
        
        # Вычисляем доступное количество символов для имени
        available = max_length - len(ext) - 3  # 3 для "..."
        
        if available < 1:
            # Если расширение слишком длинное, просто обрезаем
            return filename[:max_length-3] + "..."
        
        # Берём начало имени и добавляем расширение
        return name[:available] + "..." + ext

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

        def on_checkbox_size_active(instance, value):
            """Обработчик для чекбокса 'Разбить по размеру'"""
            print(f"checkbox_size {'активирован' if value else 'деактивирован'}")
            if value and self.checkbox_row.active:
                # Если активируем этот чекбокс, деактивируем другой
                self.checkbox_row.active = False
        
        def on_checkbox_row_active(instance, value):
            """Обработчик для чекбокса 'Разбить по строке'"""
            print(f"checkbox_row {'активирован' if value else 'деактивирован'}")
            if value and self.checkbox_size.active:
                # Если активируем этот чекбокс, деактивируем другой
                self.checkbox_size.active = False

        # Сохранение ссылок на чекбоксы
        self.checkbox_size = MDCheckbox(
            size_hint=(None, None),
            size=("48dp", "48dp"),
            pos_hint={"center_y": 0.5},
        )
        self.checkbox_size.id = "checkbox_size"
        self.checkbox_size.bind(active=on_checkbox_size_active)

        self.checkbox_row = MDCheckbox(
            size_hint=(None, None),
            size=("48dp", "48dp"),
            pos_hint={"center_y": 0.5},
        )
        self.checkbox_row.id = "checkbox_row"
        self.checkbox_row.bind(active=on_checkbox_row_active)

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
        
        # Проверяем, что выбран хотя бы один режим
        if not size_split and not row_split:
            print("Не выбран режим разбиения")
            return

        # Проверка значений в полях ввода только для режима "Разбить по размеру"
        target = 0
        tolerance = 0
        
        if size_split:
            target_text = self.target_input.text
            tolerance_text = self.tolerance_input.text
            
            if not target_text.isdigit() or not tolerance_text.isdigit():
                print("Некорректные значения в полях ввода для режима 'Разбить по размеру'")
                return
            
            target = int(target_text)
            tolerance = int(tolerance_text)

        # Получаем текст из text_area или из загруженных файлов
        selected_texts, selected_ids = self.get_text_from_area_or_fragments()
        print(f"Выбранные тексты: {len(selected_texts)} шт.")
        print(f"Выбранные IDs: {selected_ids}")

        if not selected_texts:
            print("Не выбран текст для разбиения")
            return

        # Закрываем диалог фрагментатора
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        # Отображаем прелоадер
        self.show_preloader()

        # Запускаем вычисления в потоке
        Thread(
            target=self._fragment_texts_in_thread,
            args=(selected_texts, selected_ids, size_split, row_split, target, tolerance),
            daemon=True
        ).start()

    def split_by_size(self, text, target, tolerance):
        """
        Разбивает текст на фрагменты по законченным предложениям.
        :param text: Исходный текст
        :param target: Целевое количество слов
        :param tolerance: Допуск (минимум слов)
        :return: Список кортежей (fragment_text, is_successful)
        """
        if not text:
            return []
        
        # Разбиваем текст на предложения (по точке, вопросительному и восклицательному знаку)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        fragments = []
        buffer = []
        buffer_word_count = 0
        
        min_words = target - tolerance
        max_words = target + tolerance
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Если добавление предложения не превысит максимум, добавляем в буфер
            if buffer_word_count + sentence_words <= max_words:
                buffer.append(sentence)
                buffer_word_count += sentence_words
            else:
                # Если буфер достаточно полон, сохраняем фрагмент
                if buffer:
                    fragment_text = ' '.join(buffer)
                    is_successful = min_words <= buffer_word_count <= max_words
                    fragments.append((fragment_text, is_successful, buffer_word_count))
                
                # Начинаем новый фрагмент с текущего предложения
                buffer = [sentence]
                buffer_word_count = sentence_words
        
        # Добавляем последний фрагмент, если он не пустой
        if buffer:
            fragment_text = ' '.join(buffer)
            is_successful = min_words <= buffer_word_count <= max_words
            fragments.append((fragment_text, is_successful, buffer_word_count))
        
        return fragments

    def process_large_texts(self, selected_texts, target, tolerance, max_workers=1500):
        """
        Параллельная фрагментация больших текстов.
        :param selected_texts: Список текстов для фрагментации.
        :param target: Желаемое количество слов в одном фрагменте.
        :param tolerance: Допуск (+/-).
        :param max_workers: Количество потоков для параллельной обработки.
        :return: Список кортежей (fragment_text, is_successful, word_count).
        """

        def fragment_text(text):
            # Проверяем длину текста и ограничиваем обработку
            if len(text.split()) > target * 10:  # Примерное ограничение
                print("Обрабатывается большой текст...")
            return self.split_by_size(text, target, tolerance)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(fragment_text, selected_texts)
        return list(chain.from_iterable(results))  # Сразу объединяем фрагменты

    def _fragment_texts_in_thread(self, selected_texts, selected_ids, size_split, row_split, target, tolerance):
        """
        Выполняет фрагментацию текста в отдельном потоке и обновляет интерфейс.
        """
        from itertools import chain
        
        # Инициализируем прогресс-бар
        total_texts = len(selected_texts)
        Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'max', total_texts), 0)
        Clock.schedule_once(lambda dt: setattr(self.progress_bar, 'value', 0), 0)

        fragmented_data = []
        if size_split and not row_split:
            # Разбиение по размеру с учетом законченных предложений
            # Обрабатываем каждый текст по отдельности с обновлением прогресса
            for idx, text in enumerate(selected_texts, start=1):
                fragments = self.split_by_size(text, target, tolerance)
                fragmented_data.extend(fragments)
                # Обновляем прогресс-бар
                Clock.schedule_once(lambda dt, val=idx: setattr(self.progress_bar, 'value', val), 0)
        elif row_split:
            # Для разбиения по строкам просто разделяем каждый выбранный текст
            # Приоритет отдаем разбиению по строкам, если оба режима активны
            for idx, text in enumerate(selected_texts, start=1):
                for line in text.splitlines():
                    if line.strip():  # Игнорируем пустые строки
                        word_count = len(line.split())
                        # Все фрагменты помечаются как успешные при разбиении по строкам
                        fragmented_data.append((line.strip(), True, word_count))
                # Обновляем прогресс-бар после каждого файла
                Clock.schedule_once(lambda dt, val=idx: setattr(self.progress_bar, 'value', val), 0)

        # Переход обратно в основной поток для обновления интерфейса
        Clock.schedule_once(lambda dt: self._update_ui_after_fragmentation(fragmented_data, selected_ids))

    def _update_ui_after_fragmentation(self, fragmented_data, selected_ids):
        """
        Обновляет интерфейс после фрагментации текста.
        :param fragmented_data: Список кортежей (text, is_successful, word_count)
        :param selected_ids: Список ID исходных файлов, которые были разбиты
        """
        # Скрываем прелоадер
        self.hide_preloader()
        
        # Закрываем диалог фрагментатора, если он ещё открыт
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        # Подсчитываем статистику
        total_fragments = len(fragmented_data)
        failed_fragments = sum(1 for _, is_successful, _ in fragmented_data if not is_successful)
        successful_fragments = total_fragments - failed_fragments

        # Показать всплывающее окно со статистикой
        stats_text = f"Создано фрагментов\n\nвсего: {total_fragments}\n\nнеудачных: {failed_fragments}"
        
        info_popup = Popup(
            title="Обработка завершена",
            content=Label(text=stats_text, font_size="16sp"),
            size_hint=(0.4, 0.4),
            auto_dismiss=True
        )
        info_popup.open()

        # Удаляем исходные файлы из self.texts
        selected_ids_set = set(selected_ids)
        self.texts = [(file_path, text) for file_path, text in self.texts if file_path not in selected_ids_set]
        
        # Добавляем новые фрагменты в self.texts
        for idx, (fragment_text, is_successful, word_count) in enumerate(fragmented_data, start=1):
            # Генерируем уникальный ключ для фрагмента
            fragment_key = f"fragment_{len(self.texts) + 1}_{idx}"
            self.texts.append((fragment_key, fragment_text))
        
        # Сбрасываем текущий выбранный индекс
        self.current_text_index = None
        self.current_selected_button = None
        
        # Перерисовываем таблицу из обновлённого self.texts
        self.render_table_from_texts()
        
        # Сбрасываем прогресс-бар
        self.progress_bar.value = 0

    def get_text_from_area_or_fragments(self):
        """
        Возвращает тексты и IDs только из файлов с отмеченными чекбоксами.
        :return: (selected_texts, selected_ids)
        """
        # Собираем идентификаторы файлов с отмеченными чекбоксами
        selected_ids = set()
        for widget in self.table_layout.walk():
            if isinstance(widget, CheckBox) and widget.active:
                frag_id = getattr(widget, 'fragment_id', None)
                if frag_id is not None:
                    selected_ids.add(frag_id)
        
        if not selected_ids:
            print("Нет отмеченных файлов для фрагментации.")
            return [], []
        
        # Возвращаем тексты только из отмеченных файлов
        selected_texts = []
        for file_path, text in self.texts:
            if file_path in selected_ids:
                selected_texts.append(text)
        
        print(f"Выбрано {len(selected_texts)} текстов для фрагментации")
        return selected_texts, list(selected_ids)

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
        # Очищаем только таблицу; text_area — это TextInput, у него нет детей
        self.table_layout.clear_widgets()

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
            button.background_color = (1, 1, 1, 1)  # Белый цвет по умолчанию
            button.bind(on_release=lambda btn, idx=idx, texts=fragmented_texts: self.on_fragment_button_press(idx, texts, btn))
            scroll_content.add_widget(BorderedCell(button))

            # Создание и добавление метки с фрагментом
            scroll_content.add_widget(BorderedCell(Label(text='txt', size_hint_y=None, height=20, font_size="10sp")))

            # Добавление метки с количеством слов
            scroll_content.add_widget(BorderedCell(Label(text=str(word_count), size_hint_y=None, height=20, font_size="10sp")))

            # Создание чекбокса с уникальным идентификатором для фрагмента
            check_box = CheckBox(size_hint_y=None, height=20)
            check_box.fragment_id = idx  # Привязываем индекс фрагмента как уникальный идентификатор
            scroll_content.add_widget(BorderedCell(check_box))

            # Обновление правого окна не выполняем здесь; оно управляется выбором строки

        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)

    def on_fragment_button_press(self, idx, fragmented_texts, instance=None):
        """
        Обработчик нажатия на кнопку фрагмента. Обновляет текстовое поле.
        """
        # Сбрасываем выделение предыдущей кнопки
        if self.current_selected_button:
            self.current_selected_button.background_color = (1, 1, 1, 1)
        
        # Выделяем новую кнопку
        if instance:
            instance.background_color = (0.3, 0.7, 1, 1)  # Светло-голубой цвет
            self.current_selected_button = instance
        
        # Получаем текст фрагмента по индексу и обновляем текстовую область
        selected_text = fragmented_texts[idx - 1]  # Индексация начинается с 1
        self.text_area.text = selected_text  # Устанавливаем текст непосредственно в поле
        # Индекс в self.texts здесь не трогаем, этот метод работает с временным списком

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
        
        # Инициализируем прогрессбар
        total_files = len(file_paths)
        self.progress_bar.max = total_files
        self.progress_bar.value = 0
        
        # Запускаем загрузку в отдельном потоке
        Thread(
            target=self._load_files_thread,
            args=(file_paths,),
            daemon=True
        ).start()
    
    def _load_files_thread(self, file_paths):
        """Загружает файлы в отдельном потоке"""
        # Сброс данных
        self.texts = []
        self.current_text_index = None
        self.current_selected_button = None
        
        # Логируем начало загрузки
        self.logger.info("Начинаем загрузку файлов.")
        
        loaded_data = []
        
        # Загружаем файлы
        for i, file_path in enumerate(file_paths, start=1):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read().strip()
                    
                    # Логируем успешную загрузку
                    self.logger.debug(f"Файл загружен: {file_path}, текст длиной {len(text)} символов.")
                    
                    words_count = len(text.split())
                    fragment = os.path.basename(file_path)
                    fragment = self.shorten_filename(fragment)
                    
                    loaded_data.append({
                        'file_path': file_path,
                        'text': text,
                        'fragment': fragment,
                        'words_count': words_count,
                        'index': i
                    })
                    
            except Exception as e:
                self.logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
            
            # Обновляем прогрессбар через главный поток
            Clock.schedule_once(lambda dt, val=i: setattr(self.progress_bar, 'value', val), 0)
        
        # Обновляем UI в главном потоке
        Clock.schedule_once(lambda dt: self._update_table_after_load(loaded_data), 0)
    
    def _update_table_after_load(self, loaded_data):
        """Обновляет таблицу после загрузки файлов (вызывается в главном потоке)"""
        # Очищаем таблицу
        self.table_layout.clear_widgets()
        
        # Создание ScrollView для таблицы
        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_content = GridLayout(cols=4, size_hint_y=None)
        scroll_content.bind(minimum_height=scroll_content.setter('height'))
        
        # Заголовки таблицы
        headers = ["##", "Фрагмент", "Слов", "Выбрать"]
        for header in headers:
            scroll_content.add_widget(BorderedCell(Label(text=header, size_hint_y=None, height=20, font_size="12sp")))
        
        # Добавляем загруженные данные
        for data in loaded_data:
            file_path = data['file_path']
            text = data['text']
            fragment = data['fragment']
            words_count = data['words_count']
            i = data['index']
            
            # Сохраняем текст
            self.texts.append((file_path, text))
            
            # Создаем UI элементы
            button = Button(text=str(i), size_hint_y=None, height=20)
            button.background_color = (1, 1, 1, 1)
            button.bind(on_release=partial(self.display_text, i - 1))
            
            checkbox = CheckBox(size_hint_y=None, height=20)
            checkbox.fragment_id = file_path
            
            # Добавляем элементы в таблицу
            scroll_content.add_widget(BorderedCell(button))
            scroll_content.add_widget(BorderedCell(Label(text=fragment, size_hint_y=None, height=20, font_size="10sp")))
            scroll_content.add_widget(BorderedCell(Label(text=str(words_count), size_hint_y=None, height=20, font_size="10sp")))
            scroll_content.add_widget(BorderedCell(checkbox))
        
        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)
        
        # Логируем состояние
        self.logger.debug(f"Состояние self.texts после загрузки: {len(self.texts)} файлов")
        
        # Сбрасываем прогресс-бар
        self.progress_bar.value = 0

    def render_table_from_texts(self):
        """Полностью перерисовывает таблицу на основе текущего self.texts без чтения файлов заново."""
        self.table_layout.clear_widgets()

        scroll_view = ScrollView(size_hint=(1, 1))
        scroll_content = GridLayout(cols=4, size_hint_y=None)
        scroll_content.bind(minimum_height=scroll_content.setter('height'))

        headers = ["##", "Фрагмент", "Слов", "Выбрать"]
        for header in headers:
            scroll_content.add_widget(BorderedCell(Label(text=header, size_hint_y=None, height=20, font_size="12sp")))

        for i, (file_path, text) in enumerate(self.texts, start=1):
            words_count = len(text.split())
            # Отображаем имя файла без пути
            display_name = os.path.basename(file_path)
            display_name = self.shorten_filename(display_name)  # Сокращаем длинное имя

            button = Button(text=str(i), size_hint_y=None, height=20)
            button.bind(on_release=partial(self.display_text, i - 1))
            
            # Если это текущая выбранная строка, выделяем кнопку
            if self.current_text_index == i - 1:
                button.background_color = (0.3, 0.7, 1, 1)  # Светло-голубой цвет
                self.current_selected_button = button
            else:
                button.background_color = (1, 1, 1, 1)  # Белый по умолчанию

            checkbox = CheckBox(size_hint_y=None, height=20)
            checkbox.fragment_id = file_path

            scroll_content.add_widget(BorderedCell(button))
            scroll_content.add_widget(BorderedCell(Label(text=display_name, size_hint_y=None, height=20, font_size="10sp")))
            scroll_content.add_widget(BorderedCell(Label(text=str(words_count), size_hint_y=None, height=20, font_size="10sp")))
            scroll_content.add_widget(BorderedCell(checkbox))

        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)

    def display_text(self, index, instance=None):
        """
        Отображает текст выбранного файла.
        """
        # Сбрасываем выделение предыдущей кнопки
        if self.current_selected_button:
            self.current_selected_button.background_color = (1, 1, 1, 1)
        
        # Выделяем новую кнопку
        if instance:
            instance.background_color = (0.3, 0.7, 1, 1)  # Светло-голубой цвет
            self.current_selected_button = instance
        
        file_path, text = self.texts[index]
        # Отображение текста в правом окне
        self.text_area.text = f"{text}"
        # Запоминаем, какой элемент выбран
        self.current_text_index = index

    #############################################################################

    ############################ Выделение чекбоксов ################################
    def select_all_checkboxes(self, instance):
        """
        Отмечает все чекбоксы в таблице.
        """
        # Используем walk() для обхода всех виджетов в дереве
        for widget in self.table_layout.walk():
            if isinstance(widget, CheckBox):
                widget.active = True  # Отмечаем чекбокс

    def disable_all_checkboxes(self, instance):
        """
        Убирает отметки всех чекбоксов в таблице.
        """
        # Используем walk() для обхода всех виджетов в дереве
        for widget in self.table_layout.walk():
            if isinstance(widget, CheckBox):
                widget.active = False  # Снимаем отметку с чекбокса

    #############################################################################

    ############################ Разделение фрагмента на 2 части по местоположению курсора ################################
    def split_text(self, instance):
        print("split_text called")
        cursor_position = self.text_area.cursor_index()  # Получаем текущую позицию курсора
        text = self.text_area.text.strip()

        if not text:
            print("Text is empty, aborting split")
            return

        # Определяем, какой элемент self.texts сейчас выбран
        if self.current_text_index is None or self.current_text_index >= len(self.texts):
            # Попытка найти по содержимому в self.texts
            try:
                self.current_text_index = next(i for i, (_, t) in enumerate(self.texts) if t == text)
            except StopIteration:
                print("Не удалось определить выбранный элемент для разделения")
                return

        # Разделение текста
        first_part = text[:cursor_position].strip()
        second_part = text[cursor_position:].strip()

        print("First part:", first_part)
        print("Second part:", second_part)

        if not first_part or not second_part:
            print("One of the parts is empty, aborting split")
            return

        # Формируем новые ключи на основе исходного пути
        original_key = self.texts[self.current_text_index][0]
        base_key = original_key.split('#')[0]
        key1 = f"{base_key}#1"
        key2 = f"{base_key}#2"

        # Обеспечим уникальность ключей в self.texts
        existing_keys = {k for k, _ in self.texts}
        if key1 in existing_keys or key2 in existing_keys:
            suffix = 1
            while True:
                key1_try = f"{base_key}#part{suffix}.1"
                key2_try = f"{base_key}#part{suffix}.2"
                if key1_try not in existing_keys and key2_try not in existing_keys:
                    key1, key2 = key1_try, key2_try
                    break
                suffix += 1

        # Обновляем self.texts: заменяем один элемент на два
        new_texts = []
        for i, (k, t) in enumerate(self.texts):
            if i == self.current_text_index:
                new_texts.append((key1, first_part))
                new_texts.append((key2, second_part))
            else:
                new_texts.append((k, t))
        self.texts = new_texts

        # Обновляем текст в text_area (оставляем первую часть)
        self.text_area.text = first_part

        # Перерисовываем таблицу из текущего состояния self.texts
        self.render_table_from_texts()

    def update_table(self, removed_key=None, new_fragments=None):
        """
        Обновляет таблицу: удаляет строку с `removed_key` и добавляет строки из `new_fragments`.
        """
        # Эта функция больше не используется для построчных манипуляций.
        # Для一致ности интерфейса теперь вся таблица перерисовывается из self.texts.
        self.render_table_from_texts()

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
        # Собираем отмеченные идентификаторы
        selected_ids = []
        for widget in self.table_layout.walk():
            if isinstance(widget, CheckBox) and getattr(widget, 'active', False):
                frag_id = getattr(widget, 'fragment_id', None)
                if frag_id is not None:
                    selected_ids.append(frag_id)

        if not selected_ids:
            return

        # Фильтруем self.texts
        self.texts = [(k, t) for (k, t) in self.texts if k not in set(selected_ids)]

        # Сброс текущего индекса, если он указывает на удалённый элемент
        if self.current_text_index is not None:
            if self.current_text_index >= len(self.texts):
                self.current_text_index = None

        # Перерисовываем таблицу
        self.render_table_from_texts()

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

            # Имя файла для отображения без пути
            display_name = os.path.basename(fragment_id)
            display_name = self.shorten_filename(display_name)  # Сокращаем длинное имя

            # Кнопка с индексом
            button = Button(text=str(i), size_hint_y=None, height=20)
            button.background_color = (1, 1, 1, 1)  # Белый цвет по умолчанию
            button.bind(on_release=partial(self.display_text, i))

            # Чекбокс для выбора
            checkbox = CheckBox(size_hint_y=None, height=20)
            checkbox.fragment_id = fragment_id  # Идентификатор фрагмента

            # Добавляем виджеты в таблицу
            scroll_content.add_widget(BorderedCell(button))
            scroll_content.add_widget(BorderedCell(Label(text=display_name, size_hint_y=None, height=20, font_size="10sp")))
            scroll_content.add_widget(BorderedCell(Label(text=str(words_count), size_hint_y=None, height=20, font_size="10sp")))
            scroll_content.add_widget(BorderedCell(checkbox))

        # Добавляем таблицу в ScrollView
        scroll_view.add_widget(scroll_content)
        self.table_layout.add_widget(scroll_view)
    #############################################################################


if __name__ == "__main__":
    DataLexApp().run()
