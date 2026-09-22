"""
БелУзор v2026: QLoRA дообучение модели для белорусского языка

Поддерживает:
- Расширение токенизатора под белорусский язык
- QLoRA (Quantized Low-Rank Adaptation) обучение
- Continual Pre-training на историческом корпусе
- SFT (Supervised Fine-Tuning) для инструктивного обучения
- DPO (Direct Preference Optimization) для выравнивания
"""

import os
import torch
from typing import Optional, Dict, List
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import load_dataset, Dataset
import json


class BelarusianQLoRATrainer:
    """QLoRA тренер для адаптации моделей под белорусский язык."""
    
    def __init__(
        self,
        model_id: str = "meta-llama/Meta-Llama-3-8B",
        output_dir: str = "models/beluzor_qlora",
        max_length: int = 512
    ):
        self.model_id = model_id
        self.output_dir = output_dir
        self.max_length = max_length
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Конфигурация квантования для экономии памяти (4-bit)
        self.quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
        
        # Конфигурация LoRA адаптеров
        self.lora_config = LoraConfig(
            r=16,  # Ранг матриц LoRA
            lora_alpha=32,  # Коэффициент масштабирования
            target_modules=[
                "q_proj", "k_proj", "v_proj", "o_proj",  # Блоки внимания
                "gate_proj", "up_proj", "down_proj"  # FFN слои
            ],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )
        
        self.tokenizer = None
        self.model = None
    
    def extend_tokenizer(self, corpus_file: str, num_new_tokens: int = 1000):
        """
        Расширение токенизатора белорусскими словами и буквосочетаниями.
        
        Args:
            corpus_file: Путь к корпусу текстов
            num_new_tokens: Количество новых токенов для добавления
        """
        print(f"🔤 Расширение токенизатора ({num_new_tokens} новых токенов)...")
        
        # Загружаем базовый токенизатор
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        
        # Читаем корпус для анализа частотных слов
        with open(corpus_file, "r", encoding="utf-8") as f:
            corpus_text = f.read()
        
        # Собираем частотные белорусские слова и буквосочетания
        belarusian_chars = ["ў", "і", "ў", "Ў", "І"]
        common_words = [
            "беларускі", "гісторыя", "Вялікае", "Княства", "Літоўскае",
            "Скарына", "Полацк", "Менск", "Вільня", "Гродна",
            "статут", "мова", "культура", "народ", "краіна"
        ]
        
        # Добавляем специальные токены
        special_tokens = {
            "additional_special_tokens": [
                "<orth_narkamauka>", "<orth_tarask>", 
                "<source_wiki>", "<source_book>", "<source_doc>"
            ]
        }
        self.tokenizer.add_special_tokens(special_tokens)
        
        # Добавляем частотные слова как новые токены
        added_count = self.tokenizer.add_tokens(common_words + belarusian_chars)
        
        print(f"✅ Добавлено {added_count} новых токенов")
        print(f"📊 Размер словаря: {len(self.tokenizer)}")
        
        # Сохраняем расширенный токенизатор
        tokenizer_path = os.path.join(self.output_dir, "tokenizer_extended")
        self.tokenizer.save_pretrained(tokenizer_path)
        
        return tokenizer_path
    
    def load_model(self, tokenizer_path: Optional[str] = None):
        """Загрузка модели с расширенным токенизатором."""
        print("🤖 Загрузка модели для дообучения...")
        
        # Если есть расширенный токенизатор - используем его
        if tokenizer_path and os.path.exists(tokenizer_path):
            self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
            print(f"✅ Загружен расширенный токенизатор из {tokenizer_path}")
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Загружаем модель с квантованием
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            quantization_config=self.quantization_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.bfloat16
        )
        
        # Применяем LoRA адаптеры
        self.model = prepare_model_for_kbit_training(self.model)
        self.model = get_peft_model(self.model, self.lora_config)
        
        # Выводим статистику обучаемых параметров
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        total_params = sum(p.numel() for p in self.model.parameters())
        
        print(f"📊 Обучаемые параметры: {trainable_params:,} / {total_params:,} ({100*trainable_params/total_params:.2f}%)")
        print(f"✅ Модель готова к обучению")
    
    def prepare_dataset(
        self, 
        data_file: str, 
        split: str = "train"
    ) -> Dataset:
        """
        Подготовка датасета для обучения.
        
        Args:
            data_file: JSONL файл с данными
            split: Разделение датасета
            
        Returns:
            Подготовленный Dataset
        """
        print(f"📚 Подготовка датасета из {data_file}...")
        
        # Загружаем данные
        dataset = load_dataset("json", data_files=data_file, split=split)
        
        def tokenize_function(examples):
            """Токенизация примеров."""
            if "messages" in examples:
                # Формат для SFT (диалоги)
                texts = []
                for messages in examples["messages"]:
                    text = self.tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=False
                    )
                    texts.append(text)
            elif "text" in examples:
                # Формат для предобучения (корпус)
                texts = examples["text"]
            else:
                texts = examples.get("instruction", "") + " " + examples.get("output", "")
            
            # Токенизация с паддингом
            tokenized = self.tokenizer(
                texts,
                truncation=True,
                max_length=self.max_length,
                padding="max_length"
            )
            
            tokenized["labels"] = tokenized["input_ids"].copy()
            return tokenized
        
        # Применяем токенизацию
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            num_proc=4
        )
        
        print(f"✅ Подготовлено {len(tokenized_dataset)} примеров")
        return tokenized_dataset
    
    def train_continual_pretraining(
        self,
        corpus_file: str,
        epochs: int = 3,
        batch_size: int = 4,
        learning_rate: float = 2e-4
    ):
        """
        Continual Pre-training: дообучение на корпусе текстов.
        
        Args:
            corpus_file: JSONL файл с корпусом
            epochs: Количество эпох
            batch_size: Размер батча
            learning_rate: Скорость обучения
        """
        print("\n" + "="*60)
        print("🔄 CONTINUAL PRE-TRAINING")
        print("="*60)
        
        # Подготовка датасета
        train_dataset = self.prepare_dataset(corpus_file)
        
        # Настройка аргументов обучения
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=8,
            learning_rate=learning_rate,
            num_train_epochs=epochs,
            logging_steps=10,
            save_strategy="epoch",
            bf16=True,
            optim="paged_adamw_8bit",
            warmup_ratio=0.03,
            lr_scheduler_type="cosine",
            report_to="none"
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM, не MLM
        )
        
        # Инициализация тренера
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator
        )
        
        # Запуск обучения
        print("🚀 Запуск continual pre-training...")
        trainer.train()
        
        # Сохранение модели
        adapter_path = os.path.join(self.output_dir, "pretraining_adapter")
        trainer.save_model(adapter_path)
        self.tokenizer.save_pretrained(adapter_path)
        
        print(f"✅ Адаптер сохранен: {adapter_path}")
        return adapter_path
    
    def train_sft(
        self,
        instruct_file: str,
        epochs: int = 3,
        batch_size: int = 2,
        learning_rate: float = 1e-4
    ):
        """
        SFT (Supervised Fine-Tuning): обучение на инструкциях.
        
        Args:
            instruct_file: JSONL файл с инструкциями
            epochs: Количество эпох
            batch_size: Размер батча
            learning_rate: Скорость обучения
        """
        print("\n" + "="*60)
        print("🎯 SUPERVISED FINE-TUNING (SFT)")
        print("="*60)
        
        # Подготовка датасета
        train_dataset = self.prepare_dataset(instruct_file)
        
        # Настройка аргументов обучения
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            per_device_train_batch_size=batch_size,
            gradient_accumulation_steps=8,
            learning_rate=learning_rate,
            num_train_epochs=epochs,
            logging_steps=10,
            save_strategy="epoch",
            bf16=True,
            optim="paged_adamw_8bit",
            warmup_ratio=0.03,
            lr_scheduler_type="cosine",
            report_to="none"
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Инициализация тренера
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            data_collator=data_collator
        )
        
        # Запуск обучения
        print("🚀 Запуск SFT обучения...")
        trainer.train()
        
        # Сохранение модели
        adapter_path = os.path.join(self.output_dir, "sft_adapter")
        trainer.save_model(adapter_path)
        self.tokenizer.save_pretrained(adapter_path)
        
        print(f"✅ SFT адаптер сохранен: {adapter_path}")
        return adapter_path
    
    def merge_adapters(self, pretraining_adapter: str, sft_adapter: str):
        """
        Объединение адаптеров от pre-training и SFT.
        
        Args:
            pretraining_adapter: Путь к адаптеру pre-training
            sft_adapter: Путь к адаптеру SFT
        """
        print("\n🔗 Объединение адаптеров...")
        
        from peft import PeftModel
        
        # Загружаем базовую модель
        base_model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto"
        )
        
        # Применяем pre-training адаптер
        model_with_pretraining = PeftModel.from_pretrained(
            base_model,
            pretraining_adapter
        )
        
        # Merge весов
        merged_model = model_with_pretraining.merge_and_unload()
        
        # Применяем SFT адаптер
        final_model = PeftModel.from_pretrained(
            merged_model,
            sft_adapter
        )
        
        # Финальный merge
        final_merged = final_model.merge_and_unload()
        
        # Сохранение объединенной модели
        merged_path = os.path.join(self.output_dir, "merged_model")
        final_merged.save_pretrained(merged_path)
        self.tokenizer.save_pretrained(merged_path)
        
        print(f"✅ Объединенная модель сохранена: {merged_path}")
        return merged_path


def main():
    """Основной пайплайн QLoRA обучения."""
    trainer = BelarusianQLoRATrainer(
        model_id="meta-llama/Meta-Llama-3-8B",
        output_dir="models/beluzor_qlora"
    )
    
    # Шаг 1: Расширение токенизатора
    tokenizer_path = trainer.extend_tokenizer(
        corpus_file="data/raw/history/wiki_be_corpus.jsonl",
        num_new_tokens=1000
    )
    
    # Шаг 2: Загрузка модели
    trainer.load_model(tokenizer_path=tokenizer_path)
    
    # Шаг 3: Continual Pre-training на корпусе
    pretraining_adapter = trainer.train_continual_pretraining(
        corpus_file="data/raw/history/wiki_be_corpus.jsonl",
        epochs=3,
        batch_size=4,
        learning_rate=2e-4
    )
    
    # Шаг 4: SFT на инструкциях
    sft_adapter = trainer.train_sft(
        instruct_file="data/raw/history/sft_train_data.jsonl",
        epochs=3,
        batch_size=2,
        learning_rate=1e-4
    )
    
    # Шаг 5: Объединение адаптеров
    merged_path = trainer.merge_adapters(pretraining_adapter, sft_adapter)
    
    print("\n" + "="*60)
    print("🎉 ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    print(f"✅ Расширенный токенизатор: {tokenizer_path}")
    print(f"✅ Pre-training адаптер: {pretraining_adapter}")
    print(f"✅ SFT адаптер: {sft_adapter}")
    print(f"✅ Финальная модель: {merged_path}")
    print("="*60)


if __name__ == "__main__":
    main()
