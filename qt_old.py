import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, QLabel, QVBoxLayout, \
    QWidget, QTableWidget, QTableWidgetItem, QListWidget, QInputDialog, QHBoxLayout, QFrame, QPushButton, \
    QSystemTrayIcon, QMenu, QAction
from nltk import WordNetLemmatizer
from textblob import TextBlob
import nltk
from nltk.corpus import wordnet
import re

# Факторный анализ
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import pandas as pd

# Кластерный анализ
from sklearn.cluster import KMeans
import numpy as np


# Указываем новый путь для данных NLTK
nltk.data.path.append('C:/python/9_analys_texts/data/nltk_data')

# Скачиваем нужные пакеты
nltk.download('wordnet', download_dir='C:/python/9_analys_texts/data/nltk_data')
nltk.download('omw-1.4')  # Чтобы WordNet мог работать с расширенным набором слов

lemmatizer = WordNetLemmatizer()


class TextAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Alexandria")
        self.setGeometry(450, 200, 1000, 600)
        # Установка иконки окна
        self.setWindowIcon(QIcon("media/image.ico"))

        # Инициализация системного трея
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("media/image.ico"))

        # Создание контекстного меню для системного трея
        tray_menu = QMenu()
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()  # Показать иконку в трее

        # Сделать лэйаут и виджеты
        self.layout = QVBoxLayout()
        self.label = QLabel("Выберите файл/файлы для анализа:")
        self.button = QPushButton("Открыть файл/файлы")
        self.sentiment_button = QPushButton("Тональность текста")
        self.synonym_button = QPushButton("Синонимы")
        self.lexeme_button = QPushButton("Лексемы")
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)

        self.factor_button = QPushButton("Факторный анализ")
        self.layout.addWidget(self.factor_button)
        self.factor_button.clicked.connect(self.perform_factor_analysis_from_text)

        self.clustering_button = QPushButton("Кластерный анализ")
        self.layout.addWidget(self.clustering_button)
        self.clustering_button.clicked.connect(self.perform_clustering_from_text)

        # Добавляем новый виджет для отображения списка слов и их выбора
        self.lexeme_list_widget = QListWidget()
        self.layout.addWidget(self.lexeme_list_widget)

        # Виджет для отображения плашек групп
        self.group_widget = QWidget()
        self.group_layout = QVBoxLayout()
        self.group_widget.setLayout(self.group_layout)
        self.layout.addWidget(self.group_widget)  # Добавляем в основной layout

        # Добавляем виджеты в лэйаут
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.sentiment_button)
        self.layout.addWidget(self.synonym_button)
        self.layout.addWidget(self.lexeme_button)
        self.layout.addWidget(self.result_display)

        # Установить центральный виджет
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        # Соединить кнопки с функциями
        self.button.clicked.connect(self.open_file)
        self.sentiment_button.clicked.connect(self.analyze_sentiment_from_text)
        self.synonym_button.clicked.connect(self.count_synonyms_from_text)
        self.lexeme_button.clicked.connect(self.count_lexemes_from_text)

        self.texts = []  # Список для хранения текста из нескольких файлов
        # В словарь для хранения групп слов
        self.word_groups = {}
        self.lexeme_list_widget.itemClicked.connect(lambda item: self.add_to_group(item.text()))

    def open_file(self):
        """
        Открывает текстовые файлы, загружает их содержимое в программу и отображает результат.
        """
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(self, "Открыть текстовые файлы", "", "Text Files (*.txt)")

        if file_paths:
            self.texts = []  # Сброс списка текстов
            for file_path in file_paths:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    self.texts.append(text)  # Добавляем текст в список
                    # Отображаем загруженный текст
                    self.result_display.append(f"Тексты загружены с: {file_path}\n{text}\n")

    def add_to_group(self, word):
        """
        Добавляет выбранное слово в группу для последующего факторного анализа.
        Если группа не существует, она создается. Также удаляет слово из общего списка лексем.
        """
        group_name, ok = QInputDialog.getText(self, "Создать группу", f"Введите название группы для {word}:")
        if ok and group_name:
            if group_name not in self.word_groups:
                self.word_groups[group_name] = []

                # Создаем плашку для новой группы
                group_frame = QFrame()
                group_layout = QHBoxLayout()
                group_frame.setLayout(group_layout)

                group_label = QLabel(group_name)
                remove_button = QPushButton('x')
                remove_button.setFixedSize(20, 20)

                group_layout.addWidget(group_label)
                group_layout.addWidget(remove_button)
                self.group_layout.addWidget(group_frame)

                # Соединяем кнопку удаления с функцией
                remove_button.clicked.connect(lambda _, grp=group_name: self.remove_group(grp, group_frame))

            # Добавляем слово в группу и удаляем его из списка лексем
            self.word_groups[group_name].append(word)
            self.result_display.append(f"Слово '{word}' добавлено в группу '{group_name}'")

            # Удаляем слово из списка лексем
            for i in range(self.lexeme_list_widget.count()):
                if self.lexeme_list_widget.item(i).text().startswith(word):
                    self.lexeme_list_widget.takeItem(i)
                    break

    def remove_group(self, group_name, group_frame):
        """
        Удаляет группу слов и соответствующую плашку из интерфейса.
        Также удаляет группу из внутреннего словаря групп лексем.
        """
        # Удаляем группу и плашку
        del self.word_groups[group_name]
        self.group_layout.removeWidget(group_frame)
        group_frame.deleteLater()
        self.result_display.append(f"Группа '{group_name}' была удалена")

    def analyze_sentiment(self, text):
        """
        Анализирует текст на тональность (позитивная, негативная или нейтральная).
        Использует библиотеку TextBlob для определения полярности текста.
        Возвращает строку с результатом анализа тональности.
        """
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        if sentiment > 0:
            return "Позитивный"
        elif sentiment < 0:
            return "Негативный"
        else:
            return "Нейтральный"

    def get_synonyms(self, word):
        """
        Получает синонимы для указанного слова с использованием WordNet (NLTK).
        Возвращает множество синонимов в нижнем регистре.
        """
        synonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().lower())
        return synonyms

    def count_synonyms(self, text, synonym_list):
        """
        Считает количество вхождений синонимов из списка в данном тексте.
        Очищает текст от пунктуации и переводит его в нижний регистр.
        Использует лемматизацию для нормализации слов.
        Возвращает словарь, где ключ — это синоним, а значение — количество вхождений.
        """
        cleaned_text = re.sub(r"[^\w\s]", "", text.lower())
        word_list = cleaned_text.split()
        lemmatized_words = [lemmatizer.lemmatize(word) for word in word_list]

        synonym_count = {synonym: 0 for synonym in synonym_list}
        for word in lemmatized_words:
            if word in synonym_count:
                synonym_count[word] += 1

        return synonym_count

    def count_lexemes(self, text):
        """
        Считает количество лексем в тексте.
        Очищает текст от пунктуации и переводит его в нижний регистр.
        Использует лемматизацию для нормализации слов.
        Возвращает отсортированный по убыванию список лексем и их количество в формате (лексема, количество).
        """
        cleaned_text = re.sub(r"[^\w\s]", "", text.lower())
        word_list = cleaned_text.split()
        lemmatized_words = [lemmatizer.lemmatize(word) for word in word_list]

        lexeme_count = {}
        for word in lemmatized_words:
            if word in lexeme_count:
                lexeme_count[word] += 1
            else:
                lexeme_count[word] = 1

        sorted_lexemes = sorted(lexeme_count.items(), key=lambda item: item[1], reverse=True)
        return sorted_lexemes

    def analyze_sentiment_from_text(self):
        """
        Анализирует тональность всех загруженных текстов.
        Для каждого текста вычисляется тональность (позитивная, негативная или нейтральная),
        результат добавляется в список.
        Выводит результаты анализа тональности в интерфейсе.
        """
        results = []
        for text in self.texts:
            sentiment = self.analyze_sentiment(text)
            results.append(f"Тональность: {sentiment}")
        self.result_display.setText("\n".join(results))

    def count_synonyms_from_text(self):
        """
        Считает количество указанных синонимов (например, для слова 'happy') в загруженных текстах.
        Для каждого текста вычисляет, сколько раз встречаются синонимы из заранее
        заданного списка (включая синонимы из WordNet).
        Результаты выводятся в интерфейсе в виде списка, где указано количество каждого синонима.
        """
        synonym_list = self.get_synonyms('happy')
        synonym_list.update({'cheerful', 'joyful', 'blissful'})
        results = []

        for text in self.texts:
            synonym_counts = self.count_synonyms(text, synonym_list)
            result = f"Количество синонимов в тексте:\n" + "\n".join([f"{synonym} ({count})" for synonym, count in synonym_counts.items() if count > 0])
            results.append(result)

        self.result_display.setText("\n\n".join(results))

    def count_lexemes_from_text(self):
        """
        Выводит количество лексем для всех загруженных текстов.
        Лексемы сначала считаются для каждого текста отдельно, затем объединяются.
        Отображает итоговый список лексем с количеством их упоминаний в интерфейсе.
        """
        self.lexeme_list_widget.clear()  # Очищаем список перед новой загрузкой
        all_lexemes = {}

        for text in self.texts:
            lexeme_counts = self.count_lexemes(text)
            for lexeme, count in lexeme_counts:
                if lexeme in all_lexemes:
                    all_lexemes[lexeme] += count  # Если лексема уже есть, добавляем её частоту
                else:
                    all_lexemes[lexeme] = count  # Иначе добавляем её впервые

        # Добавляем в список лексемы с количеством упоминаний
        for lexeme, count in all_lexemes.items():
            self.lexeme_list_widget.addItem(f"{lexeme} ({count})")

    def prepare_texts_for_factor_analysis(self):
        """
        Подготавливает тексты для факторного анализа.
        Очищает тексты от пунктуации, лемматизирует слова и заменяет слова, принадлежащие группам, на имя группы.
        Возвращает список подготовленных текстов.
        """
        lemmatized_texts = []

        for text in self.texts:
            cleaned_text = re.sub(r"[^\w\s]", "", text.lower())  # Убираем пунктуацию
            word_list = cleaned_text.split()
            lemmatized_words = [lemmatizer.lemmatize(word) for word in word_list]
            lemmatized_texts.append(" ".join(lemmatized_words))

        grouped_texts = []

        for text in lemmatized_texts:
            new_text = text
            for group, words in self.word_groups.items():
                for word in words:
                    # Используем границы слов для точной замены
                    new_text = re.sub(rf"\b{word}\b", group, new_text)
            grouped_texts.append(new_text)

        return grouped_texts

    def perform_factor_analysis(self, texts):
        """
        Проводит факторный анализ на основе переданных текстов.
        Использует метод главных компонент (PCA) после преобразования текстов в
        числовые данные через TF-IDF векторизацию.
        Возвращает DataFrame с результатами факторного анализа и список признаков (слов).
        """
        if len(texts) < 2:
            raise ValueError("Недостаточно данных для факторного анализа (необходимо хотя бы 2 документа)")

        # Преобразование текста в числовые данные через TF-IDF
        vectorizer = TfidfVectorizer(max_features=100)

        try:
            X = vectorizer.fit_transform(texts).toarray()  # Преобразуем сразу все тексты
        except Exception as e:
            raise ValueError(f"Ошибка при векторизации текстов: {str(e)}")

        n_samples, n_features = X.shape
        n_components = min(n_samples, n_features)  # Количество факторов не должно превышать min(n_samples, n_features)

        if n_components < 2:
            raise ValueError("Недостаточно данных для факторного анализа после векторизации")

        # Применение метода главных компонент (PCA)
        try:
            pca = PCA(n_components=n_components)  # Устанавливаем допустимое количество факторов
            X_pca = pca.fit_transform(X)
        except Exception as e:
            raise ValueError(f"Ошибка при применении PCA: {str(e)}")

        # Получение признаков (слов)
        feature_names = vectorizer.get_feature_names_out()

        # Создание DataFrame для отображения результатов
        df = pd.DataFrame(X_pca, columns=[f"Factor {i + 1}" for i in range(n_components)])

        return df, feature_names  # Возвращаем и DataFrame, и список признаков

    def perform_factor_analysis_from_text(self):
        """
        Выполняет факторный анализ на основе загруженных и подготовленных текстов.
        Отображает результаты в интерфейсе. В случае ошибки выводит сообщение об ошибке.
        """
        try:
            grouped_texts = self.prepare_texts_for_factor_analysis()  # Подготавливаем тексты с учетом групп
            df_factors, feature_names = self.perform_factor_analysis(grouped_texts)
            self.display_factor_analysis_results(df_factors, feature_names)
        except Exception as e:
            self.result_display.setText(f"Ошибка при выполнении факторного анализа: {str(e)}")

    # Отображение результатов в таблице
    def display_factor_analysis_results(self, df, feature_names):
        """
        Отображает результаты факторного анализа в виде таблицы.
        Таблица включает факторные нагрузки для каждого документа и список признаков (слов).
        """
        # Создаем QTableWidget для отображения результатов факторного анализа
        num_rows = df.shape[0]  # Количество строк = количество документов
        num_columns = df.shape[1] + 1  # +1 для первой колонки с признаками (словами)

        table = QTableWidget()
        table.setRowCount(num_rows)  # Устанавливаем количество строк (количество документов)
        table.setColumnCount(num_columns)  # Устанавливаем количество колонок (количество факторов + 1 для слов)

        # Устанавливаем заголовки столбцов для факторов
        table.setHorizontalHeaderLabels(["Фактор. нагрузки"] + [f"Factor {i + 1}" for i in range(df.shape[1])])

        # Заполняем первую колонку (слева) словами (признаками)
        for i, word in enumerate(feature_names):
            item = QTableWidgetItem(word)
            table.setItem(i, 0, item)  # Признаки будут в первой колонке (индекс 0)

        # Заполняем таблицу значениями факторного анализа
        for i in range(df.shape[0]):  # Для каждой строки документа
            for j in range(df.shape[1]):  # Для каждого фактора
                item = QTableWidgetItem(f"{df.iloc[i, j]:.6f}")
                table.setItem(i, j + 1, item)  # Числа начинаются со второго столбца

        # Устанавливаем созданную таблицу как центральный виджет
        self.setCentralWidget(table)

    def perform_clustering(self, texts, n_clusters=3):
        """
        Выполняет кластеризацию текстов с использованием алгоритма KMeans.
        Преобразует тексты в числовые векторы через TF-IDF и разделяет их на заданное количество кластеров.
        """
        # Преобразование текста в числовые данные через TF-IDF
        vectorizer = TfidfVectorizer(max_features=100)
        X = vectorizer.fit_transform(texts).toarray()

        # Применение KMeans для кластеризации
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        kmeans.fit(X)

        # Получаем метки кластеров
        labels = kmeans.labels_
        return labels

    def perform_clustering_from_text(self):
        """
        Выполняет кластеризацию на основе загруженных и подготовленных текстов.
        Отображает документы, распределённые по кластерам. В случае ошибки выводит сообщение об ошибке.
        """
        try:
            # Подготовка текстов
            lemmatized_texts = self.prepare_texts_for_factor_analysis()

            # Выполнение кластерного анализа
            labels = self.perform_clustering(lemmatized_texts)

            # Отображение документов по кластерам
            self.display_documents_by_cluster(labels)  # Вызываем функцию для отображения содержимого документов

        except Exception as e:
            self.result_display.setText(f"Ошибка при выполнении кластерного анализа: {str(e)}")

    def display_documents_by_cluster(self, labels):
        """
        Отображает документы, распределенные по кластерам, с использованием HTML-форматирования для визуализации.
        Каждому кластеру назначается определённый цвет для удобного различия.
        """
        clusters = {}

        # Создаем кластеры и добавляем тексты
        for i, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(f"Документ {i + 1}: {self.texts[i]}")  # Добавляем содержимое документа с его номером

        result = []
        # Определяем цвета для кластеров
        cluster_colors = ["#FFDDC1", "#C1E1FF", "#D4FFC1", "#FFF1C1", "#C1C1FF"]

        for idx, (cluster, docs) in enumerate(clusters.items()):
            color = cluster_colors[
                idx % len(cluster_colors)]  # Используем цвет из списка, если кластеров больше, чем цветов
            # Добавляем заголовок для каждого кластера с цветом
            result.append(f"<div style='background-color: {color}; padding: 10px; border-radius: 5px;'>" +
                          f"<strong>Кластер {cluster}</strong><br>" + "<br>".join(docs) +
                          "</div><br>")  # Добавляем разделитель

        # Устанавливаем HTML-содержимое в текстовое поле
        self.result_display.setHtml("\n".join(result))  # Объединяем результат для отображения


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("media/image.ico"))
    window = TextAnalyzerApp()
    window.show()
    sys.exit(app.exec_())

