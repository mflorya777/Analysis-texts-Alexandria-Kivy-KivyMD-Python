# 🚀 Быстрый старт DataLex Wails

## ⚠️ Важно! Wails требует правильной настройки проекта

Вы столкнулись с ошибкой запуска `wails dev`. Это нормально! Нужно сначала правильно инициализировать проект.

## 📝 Проблема

Проект создан вручную, но Wails требует определённой структуры для работы.

## ✅ Решение: Переинициализация проекта

### Вариант 1: Правильная инициализация Wails (РЕКОМЕНДУЕТСЯ)

Вы находитесь в папке `DataLex_Wails`. Сделайте следующее:

1. **Сохраните созданные файлы** (app.go, python_service и т.д.)

2. **Создайте новый Wails проект:**
```bash
cd c:\python_projects
wails init -n DataLex_Wails_New -t vanilla-ts
```

3. **Скопируйте ваши файлы в новый проект:**
```bash
# Скопируйте app.go и другие Go файлы
copy DataLex_Wails\app.go DataLex_Wails_New\
copy DataLex_Wails\go.mod DataLex_Wails_New\

# Скопируйте Python сервис
xcopy DataLex_Wails\python_service DataLex_Wails_New\python_service /E /I

# Скопируйте React компоненты
xcopy DataLex_Wails\frontend\src DataLex_Wails_New\frontend\src /E /I
```

4. **Запустите:**
```bash
cd DataLex_Wails_New
wails dev
```

### Вариант 2: Быстрый фикс текущего проекта

Попробуйте создать минимальную структуру:

```bash
cd c:\python_projects\DataLex_Wails
mkdir frontend\dist
cd frontend
npm install
npm run build
cd ..
wails dev
```

## 🔍 Что нужно для работы

Wails dev режим требует:
- ✅ Go 1.21+
- ✅ Node.js 18+
- ✅ Собранный frontend (или dev сервер)
- ✅ Правильный wails.json

## 📚 Инструкция по установке Wails

Если `wails version` не работает:

```bash
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

Добавьте в PATH:
```
%USERPROFILE%\go\bin
```

## 🆘 Если ничего не помогает

Временное решение - использовать только Kivy версию (DataLex_Kivy_KivyMD_Python) которая уже работает.

Wails версия потребует дополнительной настройки окружения.

## 📞 Что делать дальше

1. Проверьте что у вас установлен Go 1.21+
2. Установите Wails CLI
3. Используйте `wails init` для создания правильной структуры
4. Мигрируйте код

**Текущий проект - это концепция, для работы нужна правильная инициализация!**

