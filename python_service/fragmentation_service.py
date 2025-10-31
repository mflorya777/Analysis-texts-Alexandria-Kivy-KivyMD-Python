#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python сервис для фрагментации текстов.
Вызывается из Go Wails приложения через subprocess/API.
"""
import re
import sys
import json
import concurrent.futures
from typing import List, Tuple, Generator


# Компилируем регулярные выражения один раз для оптимизации
SENTENCE_PATTERN = re.compile(r'(?<=[.!?])\s+')


class FragmentationService:
    """Сервис для фрагментации текстов."""
    
    @staticmethod
    def split_by_size(text: str, target: int, tolerance: int) -> Generator[Tuple[str, bool, int], None, None]:
        """
        Разбивает текст на фрагменты по законченным предложениям с использованием генератора.
        
        Args:
            text: Исходный текст
            target: Целевое количество слов
            tolerance: Допуск (минимум слов)
            
        Yields:
            Кортеж (fragment_text, is_successful, word_count)
        """
        if not text:
            return
        
        # Используем предварительно скомпилированный regex (Оптимизация 8)
        sentences = SENTENCE_PATTERN.split(text.strip())
        
        buffer = []
        buffer_word_count = 0
        
        min_words = target - tolerance
        max_words = target + tolerance
        
        for sentence in sentences:
            sentence_words = len(sentence.split())
            
            # Если добавление предложения не превысит максимум, добавляем в буфер
            if buffer_word_count + sentence_words <= max_words:
                buffer.append(sentence)
                buffer_word_count += sentence_words
            else:
                # Если буфер достаточно полон, возвращаем фрагмент через yield
                if buffer:
                    fragment_text = ' '.join(buffer)
                    is_successful = min_words <= buffer_word_count <= max_words
                    yield (fragment_text, is_successful, buffer_word_count)
                
                # Начинаем новый фрагмент с текущего предложения
                buffer = [sentence]
                buffer_word_count = sentence_words
        
        # Возвращаем последний фрагмент, если он не пустой
        if buffer:
            fragment_text = ' '.join(buffer)
            is_successful = min_words <= buffer_word_count <= max_words
            yield (fragment_text, is_successful, buffer_word_count)
    
    @staticmethod
    def split_by_row(text: str) -> Generator[Tuple[str, bool, int], None, None]:
        """
        Разбивает текст по строкам, игнорируя пустые строки.
        
        Args:
            text: Исходный текст
            
        Yields:
            Кортеж (fragment_text, is_successful, word_count)
        """
        for line in text.splitlines():
            if line.strip():  # Игнорируем пустые строки
                word_count = len(line.split())
                # Все фрагменты помечаются как успешные при разбиении по строкам
                yield (line.strip(), True, word_count)
    
    @staticmethod
    def process_large_texts(
        texts: List[str], 
        target: int, 
        tolerance: int, 
        mode: str = "size",
        max_workers: int = 1500
    ) -> List[Tuple[str, bool, int]]:
        """
        Параллельная фрагментация больших текстов.
        
        Args:
            texts: Список текстов для фрагментации
            target: Желаемое количество слов в одном фрагменте
            tolerance: Допуск (+/-)
            mode: Режим фрагментации ("size" или "row")
            max_workers: Количество потоков для параллельной обработки
            
        Returns:
            Список кортежей (fragment_text, is_successful, word_count)
        """
        def fragment_text(text: str) -> List[Tuple[str, bool, int]]:
            if mode == "row":
                return list(FragmentationService.split_by_row(text))
            else:
                return list(FragmentationService.split_by_size(text, target, tolerance))
        
        fragmented_data = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(fragment_text, texts)
            for result in results:
                fragmented_data.extend(result)
        
        return fragmented_data


def main():
    """Главная функция для CLI использования."""
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Usage: fragmentation_service.py <mode> <target> <tolerance> <text>"}))
        sys.exit(1)
    
    mode = sys.argv[1]
    target = int(sys.argv[2])
    tolerance = int(sys.argv[3])
    
    # Читаем текст из stdin или следующего аргумента
    if len(sys.argv) > 4:
        text = sys.argv[4]
    else:
        text = sys.stdin.read()
    
    # Фрагментируем текст
    if mode == "size":
        fragments = list(FragmentationService.split_by_size(text, target, tolerance))
    elif mode == "row":
        fragments = list(FragmentationService.split_by_row(text))
    else:
        print(json.dumps({"error": f"Unknown mode: {mode}"}))
        sys.exit(1)
    
    # Возвращаем результат в JSON формате
    result = [
        {
            "text": fragment[0],
            "is_successful": fragment[1],
            "word_count": fragment[2]
        }
        for fragment in fragments
    ]
    
    print(json.dumps(result))


if __name__ == "__main__":
    main()

