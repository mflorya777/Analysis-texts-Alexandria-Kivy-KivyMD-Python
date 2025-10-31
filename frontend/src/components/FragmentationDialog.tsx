import React, { useState } from 'react';
import './FragmentationDialog.css';

interface FragmentationDialogProps {
  onClose: () => void;
  onConfirm: (selectedIDs: string[], mode: string, target: number, tolerance: number) => void;
}

const FragmentationDialog: React.FC<FragmentationDialogProps> = ({ onClose, onConfirm }) => {
  const [mode, setMode] = useState<'size' | 'row'>('size');
  const [target, setTarget] = useState<number>(50);
  const [tolerance, setTolerance] = useState<number>(20);

  const handleSubmit = () => {
    // TODO: Получить selectedIDs из родительского компонента
    const selectedIDs: string[] = [];
    onConfirm(selectedIDs, mode, target, tolerance);
  };

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog-content" onClick={(e) => e.stopPropagation()}>
        <div className="dialog-header">
          <h2>Настройки фрагментации</h2>
          <button className="btn-close" onClick={onClose}>×</button>
        </div>

        <div className="dialog-body">
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={mode === 'size'}
                onChange={() => {
                  if (mode !== 'size') {
                    setMode('size');
                  }
                }}
              />
              Разбить по размеру
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={mode === 'row'}
                onChange={() => {
                  if (mode !== 'row') {
                    setMode('row');
                  }
                }}
              />
              Разбить по строке
            </label>
          </div>

          {mode === 'size' && (
            <div className="form-group">
              <label>
                Цель (количество слов):
                <input
                  type="number"
                  value={target}
                  onChange={(e) => setTarget(parseInt(e.target.value) || 50)}
                />
              </label>
            </div>
          )}

          {mode === 'size' && (
            <div className="form-group">
              <label>
                +- (допуск):
                <input
                  type="number"
                  value={tolerance}
                  onChange={(e) => setTolerance(parseInt(e.target.value) || 20)}
                />
              </label>
            </div>
          )}
        </div>

        <div className="dialog-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Отмена
          </button>
          <button className="btn btn-primary" onClick={handleSubmit}>
            Подтвердить
          </button>
        </div>
      </div>
    </div>
  );
};

export default FragmentationDialog;

