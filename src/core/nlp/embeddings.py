#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 БЕЛУЗОР v2026 — Сэмплінг тэксту з выкарыстаннем BGE-M3 / multilingual-E5

Падтрымка:
- Эмбеддінгі для беларускага мовы
- Пакетная апрацоўка
- Інтэграцыя з HuggingFace Transformers
"""

import numpy as np
from typing import List, Union, Optional
from pathlib import Path
import hashlib

from src.core.logger import logger


class EmbeddingModel:
    """
    Клас для працы з мадэлямі эмбеддінгаў
    
    Падтрымлівае:
    - BAAI/bge-m3 (лепшая для славянскіх моў)
    - intfloat/multilingual-e5-base/large
    - sentence-transformers/LaBSE
    """
    
    def __init__(self, model_name: str = "BAAI/bge-m3", device: str = "cpu", 
                 max_length: int = 512):
        """
        Ініцыялізацыя мадэлі эмбеддінгаў
        
        Args:
            model_name: назва мадэлі з HuggingFace
            device: "cpu" ці "cuda"
            max_length: максімальная даўжыня тэксту ў токенах
        """
        self.model_name = model_name
        self.device = device
        self.max_length = max_length
        self.model = None
        self.tokenizer = None
        
        # Кэш для хуткасці
        self._cache = {}
        self._cache_size = 1000
        
        logger.info(f"🤖 Ініцыялізацыя мадэлі: {model_name}")
    
    def load(self):
        """Загрузка мадэлі з HuggingFace"""
        try:
            from transformers import AutoModel, AutoTokenizer
            
            logger.info(f"📥 Загрузка мадэлі {self.model_name}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            
            if self.device == "cuda":
                self.model = self.model.to("cuda")
            
            self.model.eval()
            logger.info(f"✅ Мадэль загружана на {self.device}")
            
        except ImportError:
            logger.warning("⚠️ transformers не усталяваны. Выкарыстоўвайце заглушку.")
            self.model = None
        except Exception as e:
            logger.error(f"❌ Памылка загрузкі мадэлі: {e}")
            self.model = None
    
    def encode(self, texts: Union[str, List[str]], normalize: bool = True,
               batch_size: int = 8) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Стварэнне эмбеддінгаў для тэкстаў
        
        Args:
            texts: адзін тэкст ці спіс тэкстаў
            normalize: ці трэба нармалізаваць вектары
            batch_size: памер пачкі для апрацоўкі
            
        Returns:
            Вектар ці спіс вектараў
        """
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False
        
        # Праверка кэша
        cached = []
        uncached_texts = []
        uncached_indices = []
        
        for i, text in enumerate(texts):
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash in self._cache:
                cached.append((i, self._cache[text_hash]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
        
        # Апрацоўка некэшаваных
        if uncached_texts and self.model is not None:
            new_embeddings = self._encode_batch(uncached_texts, normalize, batch_size)
            
            # Запамінанне ў кэш
            for idx, emb in zip(uncached_indices, new_embeddings):
                text_hash = hashlib.md5(texts[idx].encode()).hexdigest()
                if len(self._cache) < self._cache_size:
                    self._cache[text_hash] = emb
        
        # Зборка вынікаў
        results = [None] * len(texts)
        for idx, emb in cached:
            results[idx] = emb
        
        if uncached_texts and self.model is not None:
            for idx, emb in zip(uncached_indices, new_embeddings):
                results[idx] = emb
        elif uncached_texts:
            # Заглушка калі мадэль не загружана
            for idx in uncached_indices:
                results[idx] = np.zeros(768)
        
        if single:
            return results[0]
        return results
    
    def _encode_batch(self, texts: List[str], normalize: bool, 
                      batch_size: int) -> List[np.ndarray]:
        """Пакетнае кадаванне"""
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            # Токенізацыя
            encoded = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors='pt'
            )
            
            if self.device == "cuda":
                encoded = {k: v.to("cuda") for k, v in encoded.items()}
            
            # Атрыманне эмбеддінгаў
            with np.errstate(divide='ignore', invalid='ignore'):
                with __import__('torch').no_grad():
                    outputs = self.model(**encoded)
                    
                    # Mean pooling
                    attention_mask = encoded['attention_mask']
                    token_embeddings = outputs.last_hidden_state
                    
                    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size())
                    sum_embeddings = (token_embeddings * input_mask_expanded).sum(1)
                    sum_mask = attention_mask.sum(1)
                    
                    embeddings = sum_embeddings / (sum_mask + 1e-9)
                    
                    if normalize:
                        embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
                    
                    embeddings_np = embeddings.cpu().numpy()
                    all_embeddings.extend(embeddings_np.tolist())
        
        return [np.array(e) for e in all_embeddings]
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Спецыяльнае кадаванне для пошукавых запытаў
        
        Для bge-m3 і e5 трэба дадаваць прэфікс "query: "
        """
        if "bge-m3" in self.model_name or "e5" in self.model_name:
            query = f"query: {query}"
        
        return self.encode(query)
    
    def encode_document(self, document: str) -> np.ndarray:
        """
        Спецыяльнае кадаванне для дакументаў
        
        Для bge-m3 і e5 трэба дадаваць прэфікс "passage: "
        """
        if "bge-m3" in self.model_name or "e5" in self.model_name:
            document = f"passage: {document}"
        
        return self.encode(document)
    
    def clear_cache(self):
        """Ачыстка кэша"""
        self._cache = {}
    
    def get_stats(self) -> dict:
        """Статыстыка кэша"""
        return {
            'model': self.model_name,
            'device': self.device,
            'cache_size': len(self._cache),
            'max_length': self.max_length
        }


class SemanticChunker:
    """
    Сэмплінг тэксту на сэнсавыя часткі
    
    Выкарыстоўвае вектарную адлегласць для вызначэння мяж сэнсу
    """
    
    def __init__(self, embedding_model: EmbeddingModel = None, 
                 max_chunk_size: int = 300,
                 overlap: int = 50):
        """
        Ініцыялізацыя чанкера
        
        Args:
            embedding_model: мадэль для стварэння эмбеддінгаў
            max_chunk_size: максімальны памер чанка ў сімвалах
            overlap: перакрыццё паміж чанкамі
        """
        self.embedding_model = embedding_model or EmbeddingModel()
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
        if not self.embedding_model.model:
            self.embedding_model.load()
    
    def chunk_text(self, text: str, semantic_splitting: bool = True) -> List[str]:
        """
        Разбіццё тэксту на чанкі
        
        Args:
            text: тэкст для разбіцця
            semantic_splitting: ці выкарыстоўваць сэмплінг па сэнсе
            
        Returns:
            Спіс чанкаў
        """
        if semantic_splitting and self.embedding_model.model:
            return self._semantic_chunking(text)
        else:
            return self._simple_chunking(text)
    
    def _simple_chunking(self, text: str) -> List[str]:
        """Простае разбіццё па памеры"""
        chunks = []
        
        # Разбіццё па сказы
        sentences = self._split_sentences(text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.max_chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _semantic_chunking(self, text: str) -> List[str]:
        """Сэмплінг па змене сэнсу"""
        sentences = self._split_sentences(text)
        
        if len(sentences) < 2:
            return [text]
        
        # Стварэнне эмбеддінгаў для сказаў
        sentence_embeddings = self.embedding_model.encode(sentences)
        
        # Вызначэнне мяж па змене вектараў
        boundaries = []
        for i in range(1, len(sentences)):
            similarity = np.dot(sentence_embeddings[i-1], sentence_embeddings[i])
            
            # Калі падобнасць ніжэй парога - гэта мяжа
            if similarity < 0.7:  # Парог можна наладзіць
                boundaries.append(i)
        
        # Стварэнне чанкаў
        chunks = []
        start = 0
        for boundary in boundaries:
            chunk_text = " ".join(sentences[start:boundary])
            if len(chunk_text) > 50:  # Фільтр кароткіх чанкаў
                chunks.append(chunk_text)
            start = boundary
        
        # Апошні чанк
        if start < len(sentences):
            chunk_text = " ".join(sentences[start:])
            if len(chunk_text) > 50:
                chunks.append(chunk_text)
        
        # Калі чанкаў няма - вяртаем просты падзел
        if not chunks:
            return self._simple_chunking(text)
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """Разбіццё тэксту на сказы"""
        import re
        
        # Просты падзел па знаках прыпынку
        sentences = re.split(r'[.!?;]+', text)
        
        # Ачыстка
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def chunk_with_embeddings(self, text: str) -> List[tuple]:
        """
        Разбіццё з адначасовым стварэннем эмбеддінгаў
        
        Returns:
            Спіс (чанк, эмбеддінг)
        """
        chunks = self.chunk_text(text)
        embeddings = self.embedding_model.encode(chunks)
        
        return list(zip(chunks, embeddings))


def main():
    """Тэставанне эмбеддінгаў і чанкінгу"""
    print("="*80)
    print("🧪 ТЭСТАВАННЕ ЭМБЕДДЫНГАЎ І ЧАНКІНГУ")
    print("="*80)
    
    # Ініцыялізацыя
    embedder = EmbeddingModel(model_name="BAAI/bge-m3")
    
    # Тэст без загрузкі мадэлі (заглушка)
    test_texts = [
        "Кастусь Каліноўскі нарадзіўся ў 1838 годзе",
        "Паўстанне 1863 года кіраваў Кастусь Каліноўскі",
        "Газета «Мужыцкая праўда» выдавалася ў 1863 годзе",
    ]
    
    print("\n📊 Тэст кадавання (заглушка):")
    embeddings = embedder.encode(test_texts)
    
    for i, (text, emb) in enumerate(zip(test_texts, embeddings), 1):
        print(f"  {i}. {text[:40]}... → вектар [{emb.shape}]")
    
    # Тэст чанкінгу
    print("\n✂️ Тэст чанкінгу:")
    chunker = SemanticChunker(embedding_model=embedder)
    
    long_text = """
    Кастусь Каліноўскі нарадзіўся ў 1838 годзе ў вёсцы Мастаўляны. 
    Ён быў адным з кіраўнікоў паўстання 1863 года. 
    Каліноўскі выдаваў газету «Мужыцкая праўда» для сялян. 
    У лістападзе 1863 года яго схопілі расійскія ўлады. 
    22 сакавіка 1864 года Каліноўскага пакаралі смерцю ў Вільні.
    """
    
    chunks = chunker.chunk_text(long_text)
    
    for i, chunk in enumerate(chunks, 1):
        print(f"  {i}. [{len(chunk)} сімвалаў] {chunk[:50]}...")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
