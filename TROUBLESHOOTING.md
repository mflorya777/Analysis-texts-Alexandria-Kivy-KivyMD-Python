# 🔧 Решение проблемы с запуском Wails

## ❌ Проблема

```
ERROR   open C:\python_projects\DataLex_Wails\python_service\wails.json: The system cannot find the file specified.
```

Вы находитесь не в правильной папке!

## ✅ Решение

### Шаг 1: Перейдите в КОРНЕВУЮ папку проекта

```powershell
cd c:\python_projects\DataLex_Wails
```

НЕ `python_service`!

### Шаг 2: Проверьте что wails.json существует

```powershell
dir wails.json
```

Должен быть файл `wails.json`

### Шаг 3: Установите зависимости (если ещё не установлены)

```powershell
cd frontend
npm install
cd ..
```

### Шаг 4: Попробуйте запустить

```powershell
wails dev
```

## 🔍 Если не помогло

### Проблема: "go mod download" ошибки

```powershell
go mod download
go mod tidy
```

### Проблема: "npm install" ошибки

```powershell
cd frontend
rmdir /s /q node_modules
rm package-lock.json
npm install
cd ..
```

### Проблема: TypeScript ошибки

```powershell
cd frontend
npm run build
```

### Проблема: Wails не найден

```powershell
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

Добавьте в PATH:
```
%USERPROFILE%\go\bin
```

Затем перезапустите терминал.

## 📝 Правильная структура для запуска

```
DataLex_Wails\              ← ВЫ ДОЛЖНЫ БЫТЬ ЗДЕСЬ
├── wails.json              ← Этот файл должен быть здесь
├── main.go
├── app.go
├── go.mod
├── frontend\
│   ├── package.json
│   └── src\
└── python_service\
```

## 🎯 Альтернативное решение

Если Wails продолжает вызывать проблемы, используйте рабочий проект:

```powershell
cd c:\python_projects\text_analysis_Datalex_Kivy_KivyMD_Python
python main.py
```

Wails версия - это концепция и демонстрация архитектуры. Для полноценной работы потребуется дополнительная настройка окружения.

