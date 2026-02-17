#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📚 КІРАВАНИЕ КНІГАМІ — БелЭталон v0.1

Магчымасці:
- Дадаванне новых кніг у базу
- Парсінг тэксту на факты
- Індэксацыя новых фактаў
- Пошук па кнігах
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


class BookManager:
    """Кіраванне кнігамі і дадаванне ў базу"""

    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.books_path = self.base_path / "raw" / "history"
        self.etalons_path = self.base_path / "etalons"
        
        # Стварэнне дырэкторый калі не існуюць
        self.books_path.mkdir(parents=True, exist_ok=True)
        self.etalons_path.mkdir(parents=True, exist_ok=True)

    def load_book(self, file_path: str) -> str:
        """Загрузка тэксту кнігі"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл не знойдзены: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def parse_text_to_facts(self, text: str, chunk_size: int = 500) -> List[Dict]:
        """
        Парсінг тэксту на факты
        
        Args:
            text: Тэкст кнігі
            chunk_size: Памер аднаго факту (сімпалаў)
        
        Returns:
            Спіс фактаў
        """
        facts = []
        
        # Разбіццё на сказы
        sentences = re.split(r'[.!?]\s+', text)
        
        current_fact = ""
        fact_id = 1
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_fact) + len(sentence) < chunk_size:
                current_fact += " " + sentence if current_fact else sentence
            else:
                if current_fact:
                    facts.append({
                        'id': fact_id,
                        'fact': current_fact.strip(),
                        'source': 'manual'
                    })
                    fact_id += 1
                current_fact = sentence
        
        # Апошні факт
        if current_fact and len(current_fact.strip()) > 10:
            facts.append({
                'id': fact_id,
                'fact': current_fact.strip(),
                'source': 'manual'
            })
        
        return facts

    def parse_by_chapters(self, text: str) -> List[Dict]:
        """
        Парсінг тэксту па раздзелах/главах
        
        Args:
            text: Тэкст кнігі
        
        Returns:
            Спіс фактаў з раздзелаў
        """
        facts = []
        fact_id = 1
        
        # Пошук загалоўкаў (Раздзел, Глава, § і г.д.)
        chapter_pattern = r'(?:Раздзел|Глава|§|Роздiл)\s*\d*[.:]?\s*(.+?)(?=\n|$)'
        chapters = re.split(r'(?:Раздзел|Глава|§|Роздiл)\s*\d*[.:]?', text)
        
        for i, chapter in enumerate(chapters[1:], 1):  # Прапускам першы элемент
            chapter = chapter.strip()
            if not chapter:
                continue
            
            # Разбіццё раздзела на сказы
            sentences = re.split(r'[.!?]\s+', chapter[:2000])  # Абмежаванне даўжыні
            
            chapter_text = ""
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                chapter_text += " " + sentence
                
                # Калі набралі дастаткова тэксту
                if len(chapter_text) > 300:
                    facts.append({
                        'id': fact_id,
                        'fact': chapter_text.strip(),
                        'source': f'chapter_{i}',
                        'chapter': i
                    })
                    fact_id += 1
                    chapter_text = ""
            
            # Апошні кавалак раздзела
            if chapter_text.strip():
                facts.append({
                    'id': fact_id,
                    'fact': chapter_text.strip(),
                    'source': f'chapter_{i}',
                    'chapter': i
                })
                fact_id += 1
        
        return facts

    def add_book_to_facts(self, book_text: str, book_name: str, 
                          parse_mode: str = 'sentences') -> List[Dict]:
        """
        Дадаванне кнігі ў базу фактаў
        
        Args:
            book_text: Тэкст кнігі
            book_name: Назва кнігі
            parse_mode: 'sentences' ці 'chapters'
        
        Returns:
            Спіс новых фактаў
        """
        if parse_mode == 'chapters':
            new_facts = self.parse_by_chapters(book_text)
        else:
            new_facts = self.parse_text_to_facts(book_text)
        
        # Даданне інфармацыі пра крыніцу
        for fact in new_facts:
            fact['book'] = book_name
            fact['fact'] = f"[{book_name}] {fact['fact']}"
        
        return new_facts

    def save_facts(self, facts: List[Dict], output_file: str = None):
        """Захаванне фактаў у файл"""
        if output_file is None:
            output_file = self.etalons_path / "facts.json"
        else:
            output_file = Path(output_file)
        
        # Загрузка існуючых фактаў
        existing_facts = []
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_facts = json.load(f)
        
        # Аб'яднанне
        existing_facts.extend(facts)
        
        # Захаванне
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_facts, f, ensure_ascii=False, indent=2)
        
        return len(existing_facts)

    def load_existing_facts(self) -> List[Dict]:
        """Загрузка існуючых фактаў"""
        facts_file = self.etalons_path / "facts.json"
        if facts_file.exists():
            with open(facts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def get_book_list(self) -> List[Dict]:
        """Атрыманне спісу кніг"""
        books = []
        
        if self.books_path.exists():
            for file_path in sorted(self.books_path.glob('*.txt')):
                size = file_path.stat().st_size / 1024 / 1024  # MB
                books.append({
                    'name': file_path.stem,
                    'path': str(file_path),
                    'size_mb': round(size, 2)
                })
        
        return books

    def delete_book(self, book_name: str) -> bool:
        """Выдаленне кнігі"""
        book_path = self.books_path / f"{book_name}.txt"
        if book_path.exists():
            book_path.unlink()
            return True
        return False

    def search_in_books(self, query: str, book_name: str = None) -> List[Dict]:
        """
        Пошук па кнігах
        
        Args:
            query: Пошукавы запыт
            book_name: Назва кнігі (апцыянальна)
        
        Returns:
            Спіс супадзенняў
        """
        results = []
        books = self.get_book_list()
        
        if book_name:
            books = [b for b in books if b['name'] == book_name]
        
        query_lower = query.lower()
        
        for book in books:
            try:
                text = self.load_book(book['path'])
                
                # Пошук па сэнтенцыях
                sentences = re.split(r'[.!?]\s+', text)
                
                for i, sentence in enumerate(sentences):
                    if query_lower in sentence.lower():
                        results.append({
                            'book': book['name'],
                            'sentence': sentence.strip(),
                            'position': i
                        })
            except Exception as e:
                continue
        
        return results

    def get_statistics(self) -> Dict:
        """Статыстыка па кнігах"""
        books = self.get_book_list()
        total_size = sum(b['size_mb'] for b in books)
        
        facts_count = len(self.load_existing_facts())
        
        return {
            'books_count': len(books),
            'total_size_mb': round(total_size, 2),
            'facts_count': facts_count,
            'books': books
        }


def main():
    """Тэставанне менеджара кніг"""
    print("="*80)
    print("📚 КІРАВАНИЕ КНІГАМІ — Тэставанне")
    print("="*80)
    
    manager = BookManager()
    
    # Статыстыка
    stats = manager.get_statistics()
    print(f"\n📊 Статыстыка:")
    print(f"   • Кніг: {stats['books_count']}")
    print(f"   • Агульны памер: {stats['total_size_mb']:.2f} MB")
    print(f"   • Фактаў у базе: {stats['facts_count']:,}")
    
    # Спіс кніг
    print(f"\n📚 Кнігі:")
    for book in stats['books']:
        print(f"   • {book['name']} ({book['size_mb']:.2f} MB)")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
