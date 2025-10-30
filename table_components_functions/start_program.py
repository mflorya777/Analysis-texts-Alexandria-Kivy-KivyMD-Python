from kivy.uix.label import Label
from table_components_functions.utils import BorderedCell


def initialize_table(table_layout):
    """
    Устанавливает начальное состояние таблицы с заголовками и значением по умолчанию.
    :param table_layout: Объект GridLayout, в который будут добавлены элементы.
    """
    # Очистка текущей таблицы (если требуется)
    table_layout.clear_widgets()

    # Заголовки таблицы
    headers = ["##", "Фрагмент", "Слов", "Выбрать"]
    for header in headers:
        table_layout.add_widget(BorderedCell(Label(text=header, size_hint_y=None, height=20, font_size="12sp")))

    # Добавляем начальную строку с данными
    table_layout.add_widget(BorderedCell(Label(text="0", size_hint_y=None, height=20)))
    table_layout.add_widget(BorderedCell(Label(text="Пустой", size_hint_y=None, height=20)))
    table_layout.add_widget(BorderedCell(Label(text="2", size_hint_y=None, height=20)))
    # table_layout.add_widget(CheckBox(size_hint_y=None, height=20))
