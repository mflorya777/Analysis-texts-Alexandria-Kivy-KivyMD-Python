def save_state(self, instance):
    """
    Сохраняет текущее состояние программы (например, тексты и содержимое текстового поля) в файл.
    """
    state = {
        'texts': self.texts,  # Список текстов
        'text_area_content': self.text_area.text  # Содержимое текстового поля
    }

    try:
        with open("saved_state.json", "w", encoding="utf-8") as file:
            json.dump(state, file, ensure_ascii=False, indent=4)
        print("Состояние успешно сохранено.")
    except Exception as e:
        print(f"Ошибка при сохранении состояния: {e}")


def load_state(self, instance=None, file_path=None):
    """
    Загружает ранее сохранённое состояние программы при нажатии на кнопку.
    """
    if not file_path:
        file_path = "saved_state.json"  # Если путь не указан, используем дефолтный файл

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            state = json.load(file)
            self.texts = state.get('texts', [])
            self.text_area.text = state.get('text_area_content', "Нет текста")
        print("Состояние успешно загружено.")
    except Exception as e:
        print(f"Ошибка при загрузке состояния: {e}")


def open_load_file_dialog(self, instance):
    """
    Открывает окно выбора файла для загрузки состояния.
    """
    file_chooser = FileChooserIconView()
    file_chooser.bind(on_selection=self.load_file)

    # Кнопка "Добавить" для подтверждения выбора
    add_button = Button(text="Добавить", size_hint=(None, None), height=50)
    add_button.bind(on_release=lambda x: self.load_file(file_chooser, file_chooser.selection))

    # Размещение кнопки и FileChooser в BoxLayout
    layout = BoxLayout(orientation='vertical')
    layout.add_widget(file_chooser)
    layout.add_widget(add_button)

    load_file_popup = Popup(title="Выберите файл", content=layout, size_hint=(0.8, 0.8))
    load_file_popup.open()


def load_file(self, file_chooser, selection):
    """
    Загружает файл, выбранный пользователем.
    """
    if selection:
        file_path = selection[0]
        self.load_state(file_path=file_path)  # Загружаем состояние из выбранного файла
        print(f"Загружен файл: {file_path}")
