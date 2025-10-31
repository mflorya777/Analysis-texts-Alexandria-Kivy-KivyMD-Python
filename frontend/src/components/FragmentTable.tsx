import React, { useState } from 'react';
import './FragmentTable.css';

interface TextFragment {
  id: string;
  filePath: string;
  content: string;
  wordCount: number;
  displayName: string;
}

interface FragmentTableProps {
  fragments: TextFragment[];
  selectedFragmentId: string | null;
  currentPage: number;
  totalPages: number;
  onFragmentClick: (index: number) => void;
  onPageChange: (page: number) => void;
  onShowDialog: () => void;
  onDelete: (selectedIDs: string[]) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
}

const FragmentTable: React.FC<FragmentTableProps> = ({
  fragments,
  selectedFragmentId,
  currentPage,
  totalPages,
  onFragmentClick,
  onPageChange,
  onShowDialog,
  onDelete,
  onSelectAll,
  onDeselectAll,
}) => {
  const [selectedIDs, setSelectedIDs] = useState<Set<string>>(new Set());

  const handleCheckboxChange = (id: string, checked: boolean) => {
    const newSelected = new Set(selectedIDs);
    if (checked) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedIDs(newSelected);
  };

  const handleSelectAll = () => {
    const allIDs = new Set(fragments.map(f => f.id));
    setSelectedIDs(allIDs);
    onSelectAll();
  };

  const handleDeselectAll = () => {
    setSelectedIDs(new Set());
    onDeselectAll();
  };

  const handleDelete = () => {
    if (selectedIDs.size > 0) {
      onDelete(Array.from(selectedIDs));
      setSelectedIDs(new Set());
    }
  };

  return (
    <div className="fragment-table-container">
      <div className="table-controls">
        <button className="btn btn-secondary" onClick={onShowDialog}>
          Обработка
        </button>
        <button className="btn btn-secondary" onClick={handleSelectAll}>
          Отметить всё
        </button>
        <button className="btn btn-secondary" onClick={handleDeselectAll}>
          Снять отметки
        </button>
        <button className="btn btn-danger" onClick={handleDelete}>
          Удалить фрагменты
        </button>
      </div>

      <div className="table-wrapper">
        <table className="fragment-table">
          <thead>
            <tr>
              <th style={{ width: '10%' }}>##</th>
              <th style={{ width: '40%' }}>Фрагмент</th>
              <th style={{ width: '20%' }}>Слов</th>
              <th style={{ width: '30%' }}>Выбрать</th>
            </tr>
          </thead>
          <tbody>
            {fragments.map((fragment, index) => (
              <tr key={fragment.id}>
                <td>
                  <button
                    className={`row-number-btn ${
                      fragment.id === selectedFragmentId ? 'selected' : ''
                    }`}
                    onClick={() => onFragmentClick(index)}
                  >
                    {index + 1}
                  </button>
                </td>
                <td className="fragment-name">{fragment.displayName}</td>
                <td className="word-count">{fragment.wordCount}</td>
                <td className="checkbox-cell">
                  <input
                    type="checkbox"
                    checked={selectedIDs.has(fragment.id)}
                    onChange={(e) => handleCheckboxChange(fragment.id, e.target.checked)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="pagination">
        <button
          className="btn btn-pagination"
          disabled={currentPage === 0}
          onClick={() => onPageChange(currentPage - 1)}
        >
          ← Назад
        </button>
        <span className="page-info">
          Страница {currentPage + 1} из {totalPages}
        </span>
        <button
          className="btn btn-pagination"
          disabled={currentPage >= totalPages - 1}
          onClick={() => onPageChange(currentPage + 1)}
        >
          Вперёд →
        </button>
      </div>
    </div>
  );
};

export default FragmentTable;

