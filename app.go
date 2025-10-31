package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"unicode/utf8"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App struct
type App struct {
	ctx context.Context

	// Данные приложения
	texts            []TextFragment
	currentTextIndex *int

	// Пагинация
	itemsPerPage int
	currentPage  int
}

// TextFragment представляет фрагмент текста
type TextFragment struct {
	ID          string `json:"id"`
	FilePath    string `json:"filePath"`
	Content     string `json:"content"`
	WordCount   int    `json:"wordCount"`
	DisplayName string `json:"displayName"`
}

// FragmentMetadata метаданные фрагмента
type FragmentMetadata struct {
	Text         string `json:"text"`
	IsSuccessful bool   `json:"is_successful"`
	WordCount    int    `json:"word_count"`
}

// NewApp создаёт новый экземпляр приложения
func NewApp() *App {
	return &App{
		texts:        make([]TextFragment, 0),
		itemsPerPage: 100,
		currentPage:  0,
	}
}

// OnStartup вызывается при старте приложения
func (a *App) OnStartup(ctx context.Context) {
	a.ctx = ctx
}

// OnDomReady вызывается когда DOM готов
func (a *App) OnDomReady(ctx context.Context) {
}

// OnBeforeClose вызывается перед закрытием приложения
func (a *App) OnBeforeClose(ctx context.Context) (prevent bool) {
	return false
}

// LoadFiles загружает текстовые файлы
func (a *App) LoadFiles(filePaths []string) ([]TextFragment, error) {
	a.texts = make([]TextFragment, 0, len(filePaths))

	for i, filePath := range filePaths {
		content, err := os.ReadFile(filePath)
		if err != nil {
			continue // Пропускаем файлы с ошибками
		}

		text := strings.TrimSpace(string(content))
		wordCount := len(strings.Fields(text))
		displayName := getDisplayName(filePath)

		fragment := TextFragment{
			ID:          filePath,
			FilePath:    filePath,
			Content:     text,
			WordCount:   wordCount,
			DisplayName: displayName,
		}

		a.texts = append(a.texts, fragment)
		_ = i // Используем для логирования если нужно
	}

	// Возвращаем данные для текущей страницы
	return a.getPaginatedData(), nil
}

// GetText возвращает текст по индексу
func (a *App) GetText(index int) (*TextFragment, error) {
	if index < 0 || index >= len(a.texts) {
		return nil, fmt.Errorf("index out of range")
	}
	return &a.texts[index], nil
}

// GetPaginatedData возвращает данные для текущей страницы
func (a *App) GetPaginatedData() []TextFragment {
	return a.getPaginatedData()
}

// getPaginatedData внутренняя функция для получения пагинированных данных
func (a *App) getPaginatedData() []TextFragment {
	startIdx := a.currentPage * a.itemsPerPage
	endIdx := startIdx + a.itemsPerPage

	if startIdx >= len(a.texts) {
		return []TextFragment{}
	}

	if endIdx > len(a.texts) {
		endIdx = len(a.texts)
	}

	return a.texts[startIdx:endIdx]
}

// GetTotalPages возвращает общее количество страниц
func (a *App) GetTotalPages() int {
	if len(a.texts) == 0 {
		return 1
	}
	return (len(a.texts) + a.itemsPerPage - 1) / a.itemsPerPage
}

// GetCurrentPage возвращает текущую страницу
func (a *App) GetCurrentPage() int {
	return a.currentPage
}

// SetCurrentPage устанавливает текущую страницу
func (a *App) SetCurrentPage(page int) error {
	totalPages := a.GetTotalPages()
	if page < 0 || page >= totalPages {
		return fmt.Errorf("page out of range")
	}
	a.currentPage = page
	return nil
}

// OpenFileDialog открывает диалог выбора файлов
func (a *App) OpenFileDialog() ([]string, error) {
	return runtime.OpenMultipleFilesDialog(a.ctx, runtime.OpenDialogOptions{
		Title:   "Выберите текстовые файлы",
		Filters: []runtime.FileFilter{{DisplayName: "Текстовые файлы", Pattern: "*.txt"}},
	})
}

// FragmentTexts фрагментирует тексты через Python сервис
func (a *App) FragmentTexts(
	selectedIDs []string,
	mode string,
	target int,
	tolerance int,
) ([]FragmentMetadata, error) {
	// Получаем выбранные тексты
	selectedTexts := a.getSelectedTexts(selectedIDs)
	if len(selectedTexts) == 0 {
		return nil, fmt.Errorf("no texts selected")
	}

	// Вызываем Python сервис для фрагментации
	fragments, err := a.callPythonFragmentation(selectedTexts, mode, target, tolerance)
	if err != nil {
		return nil, err
	}

	// Удаляем исходные тексты и добавляем фрагменты
	a.replaceTextsWithFragments(selectedIDs, fragments)

	return fragments, nil
}

// getSelectedTexts получает выбранные тексты
func (a *App) getSelectedTexts(selectedIDs []string) []string {
	texts := make([]string, 0, len(selectedIDs))
	idMap := make(map[string]bool)

	for _, id := range selectedIDs {
		idMap[id] = true
	}

	for _, fragment := range a.texts {
		if idMap[fragment.ID] {
			texts = append(texts, fragment.Content)
		}
	}

	return texts
}

// callPythonFragmentation вызывает Python сервис для фрагментации
func (a *App) callPythonFragmentation(
	texts []string,
	mode string,
	target int,
	tolerance int,
) ([]FragmentMetadata, error) {
	// Получаем путь к Python сервису
	exePath, err := os.Executable()
	if err != nil {
		return nil, err
	}

	exeDir := filepath.Dir(exePath)
	pythonScript := filepath.Join(exeDir, "python_service", "fragmentation_service.py")

	// Проверяем существует ли скрипт
	if _, err := os.Stat(pythonScript); os.IsNotExist(err) {
		// Пытаемся найти в исходной директории (для разработки)
		pythonScript = filepath.Join("python_service", "fragmentation_service.py")
	}

	// Обрабатываем каждый текст отдельно
	allFragments := make([]FragmentMetadata, 0)

	for _, text := range texts {
		cmd := exec.Command("python", pythonScript, mode, fmt.Sprintf("%d", target), fmt.Sprintf("%d", tolerance))
		cmd.Stdin = strings.NewReader(text)

		output, err := cmd.Output()
		if err != nil {
			return nil, fmt.Errorf("python service error: %w", err)
		}

		var fragments []FragmentMetadata
		if err := json.Unmarshal(output, &fragments); err != nil {
			return nil, fmt.Errorf("failed to parse fragments: %w", err)
		}

		allFragments = append(allFragments, fragments...)
	}

	return allFragments, nil
}

// replaceTextsWithFragments заменяет исходные тексты на фрагменты
func (a *App) replaceTextsWithFragments(selectedIDs []string, fragments []FragmentMetadata) {
	// Создаём карту выбранных ID
	idMap := make(map[string]bool)
	for _, id := range selectedIDs {
		idMap[id] = true
	}

	// Фильтруем тексты, убирая выбранные
	newTexts := make([]TextFragment, 0, len(a.texts))
	for _, fragment := range a.texts {
		if !idMap[fragment.ID] {
			newTexts = append(newTexts, fragment)
		}
	}

	// Добавляем новые фрагменты
	for i, fragmentMeta := range fragments {
		newFragment := TextFragment{
			ID:          fmt.Sprintf("fragment_%d_%d", len(newTexts), i+1),
			FilePath:    fmt.Sprintf("fragment_%d_%d", len(newTexts), i+1),
			Content:     fragmentMeta.Text,
			WordCount:   fragmentMeta.WordCount,
			DisplayName: fmt.Sprintf("Fragment %d", len(newTexts)+i+1),
		}
		newTexts = append(newTexts, newFragment)
	}

	a.texts = newTexts
	a.currentPage = 0 // Сбрасываем на первую страницу
}

// DeleteFragments удаляет фрагменты по ID
func (a *App) DeleteFragments(selectedIDs []string) error {
	idMap := make(map[string]bool)
	for _, id := range selectedIDs {
		idMap[id] = true
	}

	newTexts := make([]TextFragment, 0, len(a.texts))
	for _, fragment := range a.texts {
		if !idMap[fragment.ID] {
			newTexts = append(newTexts, fragment)
		}
	}

	a.texts = newTexts
	a.currentPage = 0 // Сбрасываем на первую страницу
	return nil
}

// getDisplayName получает короткое имя файла из пути
func getDisplayName(filePath string) string {
	baseName := filepath.Base(filePath)
	return shortenFilename(baseName, 15)
}

// shortenFilename сокращает длинное имя файла
func shortenFilename(filename string, maxLength int) string {
	if utf8.RuneCountInString(filename) <= maxLength {
		return filename
	}

	ext := filepath.Ext(filename)
	name := strings.TrimSuffix(filename, ext)

	available := maxLength - utf8.RuneCountInString(ext) - 3 // 3 для "..."
	if available < 1 {
		return filename[:maxLength-3] + "..."
	}

	runes := []rune(name)
	if len(runes) > available {
		return string(runes[:available]) + "..." + ext
	}

	return filename
}
