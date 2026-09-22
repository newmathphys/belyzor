"""
БелУзор v2026: Модуль загрузки и очистки белорусского корпуса (Wiki + Datasets)

Поддерживает:
- Загрузку белорусской Википедии (наркамаўка)
- Интеграцию с instruct-датасетами (WiNE-iNEFF)
- Подготовку данных для QLoRA дообучения
- Семантическое разбиение на чанки с метаданными
- Разделение по стандартам: наркомовка/тарашкевица
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple
from datasets import load_dataset
from tqdm import tqdm
from datetime import datetime


class BelarusianCorpusDownloader:
    """Загрузка и очистка белорусских текстовых корпусов."""
    
    def __init__(self, output_dir: str = "data/raw/history"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Паттерны для определения стандарта правописания
        self.taraskievica_patterns = [
            r'\bў\b',  # ў встречается чаще в тарашкевице
            r'\bьшч\b',  # мягкий знак перед щ
            r'\bэ\b',  # э вместо е в некоторых позициях
            r'(-|\s)ж(\s|$)',  # ж после согласных
        ]
        
    def clean_wiki_text(self, text: str) -> str:
        """Очистка текста от специфического мусора Википедии."""
        if not text:
            return ""
        
        # Удаляем служебные заголовки
        text = re.sub(re.compile(r'==\s*Гл\.?\s*таксама\s*==.*', re.DOTALL | re.IGNORECASE), '', text)
        text = re.sub(re.compile(r'==\s*Зноскі\s*==.*', re.DOTALL | re.IGNORECASE), '', text)
        text = re.sub(re.compile(r'==\s*Літаратура\s*==.*', re.DOTALL | re.IGNORECASE), '', text)
        text = re.sub(re.compile(r'==\s*Спасылкі\s*==.*', re.DOTALL | re.IGNORECASE), '', text)
        text = re.sub(re.compile(r'==\s*Заўвагі\s*==.*', re.DOTALL | re.IGNORECASE), '', text)
        
        # Удаляем шаблоны и категории
        text = re.sub(r'\{\{[^}]*\}\}', '', text)
        text = re.sub(r'\[\[Катэгорыя:[^\]]*\]\]', '', text)
        text = re.sub(r'\[\[Файл:[^\]]*\]\]', '', text)
        
        # Чистим множественные переносы строк и пробелы
        text = re.sub(r'\n\s*\n', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def detect_orthography(self, text: str) -> str:
        """Определение стандарта правописания (наркомовка/тарашкевица)."""
        tarask_score = 0
        for pattern in self.taraskievica_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                tarask_score += 1
        
        if tarask_score >= 2:
            return "tarask"
        return "narkamauka"
    
    def semantic_chunking(
        self, 
        text: str, 
        source: str, 
        title: str = "",
        min_length: int = 40,
        max_length: int = 512
    ) -> List[Dict]:
        """
        Семантическое разбиение текста на чанки.
        
        Args:
            text: Очищенный текст
            source: Источник (Wikipedia, Book, etc.)
            title: Заголовок документа
            min_length: Минимальная длина чанка
            max_length: Максимальная длина чанка
            
        Returns:
            Список чанков с метаданными
        """
        chunks = []
        paragraphs = text.split("\n")
        
        current_chunk = ""
        current_length = 0
        
        for para in paragraphs:
            para = para.strip()
            if len(para) < min_length:
                continue
                
            # Если добавление абзаца превышает лимит - сохраняем текущий чанк
            if current_length + len(para) > max_length and current_chunk:
                orthography = self.detect_orthography(current_chunk)
                chunks.append({
                    "text": current_chunk.strip(),
                    "source": source,
                    "title": title,
                    "orthography": orthography,
                    "timestamp": datetime.now().isoformat(),
                    "char_count": len(current_chunk)
                })
                current_chunk = ""
                current_length = 0
            
            # Добавляем абзац к текущему чанку
            if current_chunk:
                current_chunk += "\n" + para
            else:
                current_chunk = para
            current_length = len(current_chunk)
        
        # Сохраняем последний чанк
        if current_chunk and len(current_chunk) >= min_length:
            orthography = self.detect_orthography(current_chunk)
            chunks.append({
                "text": current_chunk.strip(),
                "source": source,
                "title": title,
                "orthography": orthography,
                "timestamp": datetime.now().isoformat(),
                "char_count": len(current_chunk)
            })
        
        return chunks
    
    def download_wikipedia(self, limit: Optional[int] = None) -> Tuple[str, int]:
        """
        Загрузка белорусской Википедии.
        
        Args:
            limit: Ограничение количества статей (None = все)
            
        Returns:
            Путь к файлу и количество обработанных чанков
        """
        print("🚀 Запуск скачивания белорусской Википедии (наркамаўка)...")
        
        # Загружаем дамп белорусского раздела
        try:
            dataset = load_dataset(
                "wikipedia", 
                "20220301.be", 
                split="train", 
                streaming=False
            )
        except Exception as e:
            print(f"⚠️ Ошибка загрузки Wikipedia: {e}")
            print("📥 Используем альтернативный источник...")
            # Альтернатива: используем упрощенный датасет
            dataset = load_dataset("wikimedia/wikipedia", "20231101.be", split="train", streaming=True)
        
        if limit:
            dataset = dataset.select(range(min(limit, len(dataset))))
        
        output_file = os.path.join(self.output_dir, "wiki_be_corpus.jsonl")
        
        print(f"📦 Всего статей обнаружено: {len(dataset) if hasattr(dataset, '__len__') else 'streaming'}")
        print("🧹 Начинаем очистку и семантическое разбиение...")
        
        total_chunks = 0
        
        with open(output_file, "w", encoding="utf-8") as f:
            for article in tqdm(dataset, desc="Обработка статей", total=limit or 1000):
                title = article.get("title", "").strip()
                text = article.get("text", "")
                
                cleaned_text = self.clean_wiki_text(text)
                if not cleaned_text:
                    continue
                
                # Семантическое разбиение на чанки
                chunks = self.semantic_chunking(
                    cleaned_text,
                    source="Wikipedia",
                    title=title
                )
                
                for chunk in chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
                    total_chunks += 1
        
        print(f"\n✅ Успешно сохранено!")
        print(f"📁 Файл корпуса: {output_file}")
        print(f"📊 Сгенерировано интеллектуальных чанков: {total_chunks:,}")
        
        return output_file, total_chunks
    
    def download_instruct_datasets(self) -> str:
        """
        Загрузка instruct-датасетов для SFT (Supervised Fine-Tuning).
        
        Returns:
            Путь к файлу с инструкциями
        """
        print("📚 Загрузка instruct-датасетов на белорусском языке...")
        
        output_file = os.path.join(self.output_dir, "instruct_be_corpus.jsonl")
        total_samples = 0
        
        # Список доступных instruct-датасетов
        instruct_datasets = [
            "WiNE-iNEFF/instruct-datasets-in-belarusian",
            "cais/mmlu",  # Можно фильтровать по языку
        ]
        
        all_instructions = []
        
        for ds_name in instruct_datasets:
            try:
                print(f"  📥 Загрузка {ds_name}...")
                dataset = load_dataset(ds_name, split="train", streaming=True)
                
                for sample in tqdm(dataset, desc=f"Обработка {ds_name}", total=1000):
                    # Преобразуем в единый формат
                    instruction = sample.get("instruction", "") or sample.get("input", "")
                    output = sample.get("output", "") or sample.get("answer", "")
                    
                    if instruction and output:
                        all_instructions.append({
                            "instruction": instruction,
                            "output": output,
                            "source": ds_name,
                            "orthography": self.detect_orthography(instruction),
                            "timestamp": datetime.now().isoformat()
                        })
                        total_samples += 1
                        
                        if total_samples >= 5000:  # Лимит для примера
                            break
                            
            except Exception as e:
                print(f"  ⚠️ Ошибка загрузки {ds_name}: {e}")
                continue
        
        # Сохраняем в JSONL формате для SFT
        with open(output_file, "w", encoding="utf-8") as f:
            for item in all_instructions:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        print(f"\n✅ Instruct-датасет сохранен: {output_file}")
        print(f"📊 Всего инструкций: {total_samples:,}")
        
        return output_file
    
    def prepare_qwen_format(self, input_file: str, output_file: str) -> int:
        """
        Конвертация корпуса в формат для QLoRA обучения (Qwen/Llama формат).
        
        Args:
            input_file: Входной файл (JSONL)
            output_file: Выходной файл в формате для обучения
            
        Returns:
            Количество подготовленных примеров
        """
        print(f"🔄 Конвертация в формат для QLoRA обучения...")
        
        count = 0
        with open(input_file, "r", encoding="utf-8") as f_in, \
             open(output_file, "w", encoding="utf-8") as f_out:
            
            for line in f_in:
                data = json.loads(line.strip())
                
                # Формат для инструктивного обучения
                if "instruction" in data and "output" in data:
                    conversation = {
                        "messages": [
                            {"role": "system", "content": "Ты — верифицированный исторический ассистент БелУзор. Отвечай ТОЛЬКО на основе предоставленных фактов. Выкарыстоўвай беларускую мову."},
                            {"role": "user", "content": data["instruction"]},
                            {"role": "assistant", "content": data["output"]}
                        ],
                        "orthography": data.get("orthography", "narkamauka"),
                        "source": data.get("source", "unknown")
                    }
                    f_out.write(json.dumps(conversation, ensure_ascii=False) + "\n")
                    count += 1
                
                # Формат для продолженного предобучения (корпус)
                elif "text" in data:
                    conversation = {
                        "text": data["text"],
                        "source": data.get("source", "unknown"),
                        "orthography": data.get("orthography", "narkamauka")
                    }
                    f_out.write(json.dumps(conversation, ensure_ascii=False) + "\n")
                    count += 1
        
        print(f"✅ Подготовлено {count:,} примеров для обучения")
        return count


def main():
    """Основной пайплайн загрузки и подготовки данных."""
    downloader = BelarusianCorpusDownloader()
    
    # Шаг 1: Загрузка Википедии
    wiki_file, wiki_chunks = downloader.download_wikipedia(limit=1000)
    
    # Шаг 2: Загрузка instruct-датасетов
    instruct_file = downloader.download_instruct_datasets()
    
    # Шаг 3: Подготовка формата для QLoRA
    sft_output = os.path.join(downloader.output_dir, "sft_train_data.jsonl")
    downloader.prepare_qwen_format(instruct_file, sft_output)
    
    print("\n" + "="*60)
    print("📊 ИТОГИ ПОДГОТОВКИ ДАННЫХ:")
    print("="*60)
    print(f"✅ Wikipedia корпус: {wiki_file} ({wiki_chunks:,} чанков)")
    print(f"✅ Instruct датасет: {instruct_file}")
    print(f"✅ SFT формат: {sft_output}")
    print("="*60)
    print("🚀 Данные готовы для:")
    print("   1. Расширения токенизатора")
    print("   2. Векторизации через BGE-M3")
    print("   3. QLoRA дообучения модели")
    print("="*60)


if __name__ == "__main__":
    main()
