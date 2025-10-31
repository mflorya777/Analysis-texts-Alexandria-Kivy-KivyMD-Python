# 📋 Инструкция по установке DataLex Wails

## 📦 Шаг 1: Установка зависимостей

### Go (1.21+)
```bash
# Проверьте версию
go version

# Установите Wails CLI
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Проверьте установку
wails version
```

### Node.js (18+)
```bash
# Проверьте версию
node --version

# Установите зависимости frontend
cd frontend
npm install
cd ..
```

### Python (3.10+)
```bash
# Проверьте версию
python --version

# Установите зависимости Python сервиса
cd python_service
pip install -r requirements.txt
cd ..
```

## 🚀 Шаг 2: Запуск в режиме разработки

```bash
# В корне проекта
wails dev
```

Приложение откроется автоматически.

## 🏗️ Шаг 3: Сборка для продакшена

### Windows:
```bash
wails build -platform windows/amd64
```

Результат: `build/bin/DataLex.exe`

### Linux:
```bash
wails build -platform linux/amd64
```

Результат: `build/bin/DataLex`

### macOS:
```bash
wails build -platform darwin/amd64
```

Результат: `build/bin/DataLex.app`

## 🔧 Шаг 4: Настройка Python сервиса

### Вариант 1: Python доступен в PATH
Убедитесь что `python` команда работает:
```bash
python --version
```

### Вариант 2: Указать конкретный Python
В `app.go` измените:
```go
cmd := exec.Command("python", pythonScript, ...)
```
на:
```go
cmd := exec.Command("C:\\Python312\\python.exe", pythonScript, ...)
```

## 🐛 Решение проблем

### Проблема: "wails: command not found"
```bash
# Добавьте Go bin в PATH
export PATH=$PATH:$(go env GOPATH)/bin

# Windows PowerShell:
$env:Path += ";$(go env GOPATH)/bin"
```

### Проблема: Frontend не собирается
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
wails dev
```

### Проблема: Python сервис не вызывается
1. Проверьте что Python установлен
2. Проверьте путь к скрипту
3. Добавьте логи в Go:
```go
fmt.Println("Python script path:", pythonScript)
fmt.Println("Command output:", string(output))
```

### Проблема: "Cannot find module 'wails'"
```bash
# Очистите модули
go clean -modcache
go mod download
```

## ✅ Проверка работы

1. Запустите `wails dev`
2. Нажмите "Добавить текстов"
3. Выберите тестовые файлы
4. Проверьте таблицу фрагментов
5. Попробуйте фрагментацию

## 📝 Следующие шаги

- [ ] Настроить CI/CD
- [ ] Добавить автообновления
- [ ] Создать установщик
- [ ] Оптимизировать размер бинарника

## 💡 Полезные команды

```bash
# Полная пересборка
wails build -clean

# Сборка с подробным выводом
wails build -v

# Только frontend
cd frontend && npm run build

# Только backend тесты
go test ./...
```

## 🆘 Нужна помощь?

Проверьте:
1. Логи в консоли разработчика (F12)
2. Go логи в терминале
3. Python сервис работает отдельно

