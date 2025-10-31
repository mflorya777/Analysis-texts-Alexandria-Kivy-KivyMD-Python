# 🎯 Начало работы с DataLex Wails

## ⚠️ ВАЖНО! Прочитайте сначала!

Вы столкнулись с ошибкой при запуске `wails dev`. Это происходит потому, что вы запускали команду из неправильной папки.

## ✅ Правильная последовательность

### 1. Откройте PowerShell/Terminal

### 2. Перейдите в КОРНЕВУЮ папку проекта

```powershell
cd c:\python_projects\DataLex_Wails
```

НЕ `python_service` и НЕ `frontend`! Корневая папка `DataLex_Wails`!

### 3. Проверьте что вы в правильной папке

```powershell
dir
```

Должны увидеть:
- `wails.json` ✅
- `main.go` ✅
- `app.go` ✅
- `frontend\` ✅
- `python_service\` ✅

### 4. Теперь запускайте команды

```powershell
wails dev
```

## 🔄 Полный процесс

```powershell
# 1. Перейдите в корень
cd c:\python_projects\DataLex_Wails

# 2. Установите Go зависимости
go mod download

# 3. Установите frontend зависимости
cd frontend
npm install
cd ..

# 4. Запустите в dev режиме
wails dev
```

## 📋 Что вы ДОЛЖНЫ видеть

При правильном запуске в терминале появится:

```
Wails CLI v2.10.2

[INFO] Building application...
[INFO] Running dev server...
```

## ❌ Что НЕ делать

- ❌ Запускать `wails dev` из `python_service/`
- ❌ Запускать `wails dev` из `frontend/`
- ❌ Запускать из какой-либо другой папки

## 🎯 Короткая инструкция

**ВСЕГДА запускайте из:**
```
c:\python_projects\DataLex_Wails\
```

## 🆘 Если проблема остается

См. файл `TROUBLESHOOTING.md` для подробного решения проблем.

