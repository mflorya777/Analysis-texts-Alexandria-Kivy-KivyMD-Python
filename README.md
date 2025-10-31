# DataLex - Wails + React + Python

Современная реализация анализа текстов на Go Wails с React UI и Python сервисом для обработки данных.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────┐
│  React Frontend (TypeScript)            │
│  - FragmentTable                        │
│  - FragmentationDialog                  │
│  - ProgressBar                          │
└─────────────────┬───────────────────────┘
                  │ IPC (Wails)
┌─────────────────▼───────────────────────┐
│  Go Backend                             │
│  - File management                      │
│  - Pagination                           │
│  - UI logic                             │
└─────────────────┬───────────────────────┘
                  │ CLI/API
┌─────────────────▼───────────────────────┐
│  Python Service                         │
│  - Text fragmentation                   │
│  - ML/NLP analysis (будущее)            │
└─────────────────────────────────────────┘
```

## 📦 Установка и запуск

### Требования

- Go 1.21+
- Node.js 18+
- Python 3.10+

### 1. Установка зависимостей

#### Go:
```bash
go mod download
```

#### Frontend:
```bash
cd frontend
npm install
cd ..
```

#### Python:
```bash
cd python_service
pip install -r requirements.txt
cd ..
```

### 2. Запуск в режиме разработки

```bash
wails dev
```

### 3. Сборка для продакшена

```bash
wails build
```

Результат будет в `build/bin/DataLex.exe`

## 🚀 Структура проекта

```
DataLex_Wails/
├── app.go                    # Go backend основные методы
├── main.go                   # Точка входа Wails
├── go.mod                    # Go зависимости
├── frontend/                 # React приложение
│   ├── src/
│   │   ├── App.tsx          # Главный компонент
│   │   ├── App.css          # Основные стили
│   │   └── components/      # React компоненты
│   │       ├── FragmentTable.tsx
│   │       ├── FragmentationDialog.tsx
│   │       └── ProgressBar.tsx
│   └── package.json         # Frontend зависимости
└── python_service/          # Python сервис
    ├── fragmentation_service.py
    ├── __init__.py
    └── requirements.txt
```

## 🔧 Основные возможности

### ✅ Реализовано

- 📁 Загрузка текстовых файлов
- 📊 Таблица фрагментов с пагинацией
- 🔍 Просмотр содержимого фрагментов
- ✅ Множественный выбор (чекбоксы)
- 🔢 Разбиение по размеру (по предложениям)
- 📝 Разбиение по строкам
- 🗑️ Удаление фрагментов
- 📈 Прогресс-бар
- 💾 Кэширование данных

### 🚧 Планируется

- 🔄 Разделение текста по курсору
- 📊 Расширенная статистика
- 🧠 ML анализ текстов
- 💾 Сохранение результатов
- 🎨 Темная тема
- 🌐 Локализация

## 🔄 Миграция с Kivy

| Компонент Kivy | Wails эквивалент |
|----------------|------------------|
| MDDialog | React Modal |
| GridLayout | HTML Table |
| FileChooser | Go runtime.OpenMultipleFilesDialog |
| TextInput | HTML textarea |
| ProgressBar | React ProgressBar |
| CheckBox | HTML checkbox |

## 📝 Разработка

### Добавление новых методов в Go:

1. Добавить метод в `app.go`
2. Метод автоматически экспортируется в JS через Wails

### Добавление Python функций:

1. Создать функцию в `python_service/`
2. Добавить вызов из Go через `exec.Command`
3. Парсить JSON результат

### Изменение UI:

1. Редактировать `.tsx` и `.css` файлы
2. Перезапустить `wails dev`

## 🐛 Отладка

### Консоль разработчика:
В режиме dev доступна через F12

### Логи Go:
```bash
wails dev -devtools
```

### Python логи:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📄 Лицензия

MIT

## 👨‍💻 Автор

DataLex Team

