import { useState, useEffect } from 'react';
import './App.css';
import FragmentTable from './components/FragmentTable';
import FragmentationDialog from './components/FragmentationDialog';
import ProgressBar from './components/ProgressBar';

interface TextFragment {
  id: string;
  filePath: string;
  content: string;
  wordCount: number;
  displayName: string;
}

interface FragmentMetadata {
  text: string;
  is_successful: boolean;
  word_count: number;
}

interface Window {
  go?: {
    main: {
      App: any;
    };
  };
}

declare const window: Window;

function App() {
  const [fragments, setFragments] = useState<TextFragment[]>([]);
  const [currentText, setCurrentText] = useState<string>('');
  const [selectedFragmentId, setSelectedFragmentId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [progress, setProgress] = useState(0);

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    loadData();
  }, [currentPage]);

  const loadData = async () => {
    if (!window.go?.main?.App) return;

    try {
      const data = await window.go.main.App.GetPaginatedData();
      const page = await window.go.main.App.GetCurrentPage();
      const total = await window.go.main.App.GetTotalPages();

      setFragments(data || []);
      setCurrentPage(page || 0);
      setTotalPages(total || 1);
    } catch (error) {
      console.error('Ошибка загрузки данных:', error);
    }
  };

  const handleOpenFiles = async () => {
    if (!window.go?.main?.App) {
      console.error('window.go.main.App не доступен');
      alert('Ошибка: приложение не инициализировано. Перезапустите приложение.');
      return;
    }

    try {
      setIsLoading(true);
      const filePaths = await window.go.main.App.OpenFileDialog();

      if (!filePaths || filePaths.length === 0) {
        setIsLoading(false);
        return;
      }

      await window.go.main.App.LoadFiles(filePaths);
      await loadData();
      setIsLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки файлов:', error);
      alert(`Ошибка при загрузке файлов: ${error}`);
      setIsLoading(false);
    }
  };

  const handleFragmentClick = async (index: number) => {
    if (!window.go?.main?.App) return;

    try {
      const fragment = await window.go.main.App.GetText(index);
      if (fragment) {
        setCurrentText(fragment.content);
        setSelectedFragmentId(fragment.id);
      }
    } catch (error) {
      console.error('Ошибка получения текста:', error);
    }
  };

  const handlePageChange = async (newPage: number) => {
    if (!window.go?.main?.App) return;

    try {
      await window.go.main.App.SetCurrentPage(newPage);
      await loadData();
      setCurrentText('');
      setSelectedFragmentId(null);
    } catch (error) {
      console.error('Ошибка смены страницы:', error);
    }
  };

  const handleFragment = async (
    selectedIDs: string[],
    mode: string,
    target: number,
    tolerance: number
  ) => {
    if (!window.go?.main?.App) return;

    try {
      setIsLoading(true);
      setProgress(0);

      const fragments = await window.go.main.App.FragmentTexts(
        selectedIDs,
        mode,
        target,
        tolerance
      );

      setProgress(100);
      await loadData();
      setShowDialog(false);
      setIsLoading(false);

      // Показываем статистику
      const total = fragments.length;
      const failed = fragments.filter((f: FragmentMetadata) => !f.is_successful).length;

      alert(`Создано фрагментов\n\nвсего: ${total}\n\nнеудачных: ${failed}`);
    } catch (error) {
      console.error('Ошибка фрагментации:', error);
      setIsLoading(false);
    }
  };

  const handleDelete = async (selectedIDs: string[]) => {
    if (!window.go?.main?.App || selectedIDs.length === 0) return;

    try {
      await window.go.main.App.DeleteFragments(selectedIDs);
      await loadData();
      setCurrentText('');
      setSelectedFragmentId(null);
    } catch (error) {
      console.error('Ошибка удаления:', error);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>DataLex - Анализ текстов</h1>
        <button className="btn btn-primary" onClick={handleOpenFiles}>
          Добавить текстов
        </button>
      </header>

      <ProgressBar progress={progress} visible={isLoading} />

      <div className="app-content">
        <div className="left-panel">
          <FragmentTable
            fragments={fragments}
            selectedFragmentId={selectedFragmentId}
            currentPage={currentPage}
            totalPages={totalPages}
            onFragmentClick={handleFragmentClick}
            onPageChange={handlePageChange}
            onShowDialog={() => setShowDialog(true)}
            onDelete={handleDelete}
            onSelectAll={() => {}}
            onDeselectAll={() => {}}
          />
        </div>

        <div className="right-panel">
          <div className="text-viewer">
            {currentText || 'Выберите фрагмент для просмотра'}
          </div>
        </div>
      </div>

      {showDialog && (
        <FragmentationDialog
          onClose={() => setShowDialog(false)}
          onConfirm={handleFragment}
        />
      )}
    </div>
  );
}

export default App;

