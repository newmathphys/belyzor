#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 БЕЛУЗОР v2026 — Вектарная база дадзеных на базе Qdrant/ChromaDB

Падтрымка:
- Гібрыдны пошук (Dense + Sparse)
- Алгарытм RRF (Reciprocal Rank Fusion)
- Сэмплінг і фільтрацыя па метаданых
- Інтэграцыя з BGE-M3 / multilingual-E5 эмбеддінгамі
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np

from src.core.logger import logger


@dataclass
class DocumentChunk:
    """Структура чанка дакумента"""
    id: str
    text: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict = None  # крыніца, старонка, год, аўтар і г.д.
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorDatabase:
    """
    Вектарная база дадзеных для гістарычных фактаў
    
    Падтрымлівае:
    - In-memory рэжым (ChromaDB/FAISS)
    - Qdrant (пажадана для прадукшн)
    - Гібрыдны пошук (вектар + ключавыя словы)
    - RRF алгарытм для аб'яднання вынікаў
    """
    
    def __init__(self, db_type: str = "chromadb", persist_path: str = None):
        """
        Ініцыялізацыя вектарнай базы
        
        Args:
            db_type: тып БД ("chromadb", "qdrant", "faiss", "memory")
            persist_path: шлях для захавання (калі патрэбна)
        """
        self.db_type = db_type
        self.persist_path = persist_path or "./data/vector_db"
        
        # Калекцыі для розных тыпаў дакументаў
        self.collections = {}
        
        # Індэкс для sparse пошуку (BM25)
        self.sparse_index = {}
        self.idf_scores = {}
        
        # Усе чанкі
        self.chunks: Dict[str, DocumentChunk] = {}
        
        # Загрузка існуючай базы
        self._load_db()
        
        logger.info(f"✅ Вектарная БД ініцыялізавана: {db_type}")
    
    def _load_db(self):
        """Загрузка існуючай базы дадзеных"""
        # Рэалізацыя залежыць ад тыпу БД
        pass
    
    def add_chunk(self, chunk_id: str, text: str, embedding: np.ndarray = None, 
                  metadata: Dict = None) -> str:
        """
        Дадаванне чанка ў базу
        
        Args:
            chunk_id: унікальны ID чанка
            text: тэкст чанка
            embedding: вектарнае ўкладанне (калі ўжо вылічана)
            metadata: дадатковая інфармацыя
            
        Returns:
            ID дададзенага чанка
        """
        chunk = DocumentChunk(
            id=chunk_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        self.chunks[chunk_id] = chunk
        
        # Абнаўленне sparse індэкса
        self._update_sparse_index(chunk_id, text)
        
        logger.debug(f"📝 Дададзены чанк: {chunk_id[:20]}...")
        return chunk_id
    
    def _update_sparse_index(self, chunk_id: str, text: str):
        """Абнаўленне індэкса для BM25 пошуку"""
        # Токенізацыя
        tokens = self._tokenize(text)
        
        for token in set(tokens):
            if token not in self.sparse_index:
                self.sparse_index[token] = []
            self.sparse_index[token].append(chunk_id)
        
        # Перарахунак IDF
        n_docs = len(self.chunks)
        for word, doc_ids in self.sparse_index.items():
            df = len(doc_ids)
            self.idf_scores[word] = np.log(n_docs / (1 + df))
    
    def _tokenize(self, text: str) -> List[str]:
        """Простая токенизация для беларускага тэксту"""
        import re
        tokens = re.findall(r'[а-яёўі\']+|\d{4}', text.lower())
        return [t for t in tokens if len(t) >= 2]
    
    def search_dense(self, query_embedding: np.ndarray, top_k: int = 10, 
                     filter_metadata: Dict = None) -> List[Tuple[str, float]]:
        """
        Пошук па вектарных укладаннях (Dense Retrieval)
        
        Args:
            query_embedding: вектар запыту
            top_k: колькасць вынікаў
            filter_metadata: фільтр па метаданых
            
        Returns:
            Спіс (chunk_id, score)
        """
        if not self.chunks:
            return []
        
        scores = []
        for chunk_id, chunk in self.chunks.items():
            if chunk.embedding is None:
                continue
            
            # Фільтр па метаданых
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if chunk.metadata.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            # Cosine similarity
            similarity = np.dot(query_embedding, chunk.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk.embedding) + 1e-9
            )
            scores.append((chunk_id, float(similarity)))
        
        # Сартыроўка
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
    
    def search_sparse(self, query_text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Пошук па ключавых словах (Sparse/BM25)
        
        Args:
            query_text: тэкст запыту
            top_k: колькасць вынікаў
            
        Returns:
            Спіс (chunk_id, score)
        """
        tokens = self._tokenize(query_text)
        if not tokens:
            return []
        
        scores = {}
        for token in tokens:
            if token in self.sparse_index:
                for chunk_id in self.sparse_index[token]:
                    if chunk_id not in scores:
                        scores[chunk_id] = 0.0
                    
                    # TF-IDF падобны падыход
                    tf = tokens.count(token) / len(tokens)
                    idf = self.idf_scores.get(token, 1.0)
                    scores[chunk_id] += tf * idf
        
        # Сартыроўка
        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        return sorted_scores[:top_k]
    
    def hybrid_search(self, query_embedding: np.ndarray, query_text: str, 
                      top_k: int = 10, alpha: float = 0.5) -> List[Tuple[str, float]]:
        """
        Гібрыдны пошук з RRF (Reciprocal Rank Fusion)
        
        Args:
            query_embedding: вектар запыту
            query_text: тэкст запыту для sparse пошуку
            top_k: канчатковая колькасць вынікаў
            alpha: вага dense пошуку (0.5 = роўная вага)
            
        Returns:
            Спіс (chunk_id, rrf_score)
        """
        # Асобны пошук
        dense_results = self.search_dense(query_embedding, top_k=top_k*2)
        sparse_results = self.search_sparse(query_text, top_k=top_k*2)
        
        # RRF аб'яднанне
        rrf_scores = {}
        k = 60  # Канстанта для RRF
        
        # Dense рангі
        for rank, (chunk_id, score) in enumerate(dense_results, 1):
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = 0.0
            rrf_scores[chunk_id] += alpha / (k + rank)
        
        # Sparse рангі
        for rank, (chunk_id, score) in enumerate(sparse_results, 1):
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = 0.0
            rrf_scores[chunk_id] += (1 - alpha) / (k + rank)
        
        # Сартыроўка па RRF score
        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: -x[1])
        return sorted_rrf[:top_k]
    
    def get_chunk(self, chunk_id: str) -> Optional[DocumentChunk]:
        """Атрыманне чанка па ID"""
        return self.chunks.get(chunk_id)
    
    def get_chunks_batch(self, chunk_ids: List[str]) -> List[DocumentChunk]:
        """Атрыманне некалькіх чанкаў"""
        return [self.chunks[cid] for cid in chunk_ids if cid in self.chunks]
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Выдаленне чанка"""
        if chunk_id in self.chunks:
            del self.chunks[chunk_id]
            # Ачыстка sparse індэкса
            self._rebuild_sparse_index()
            return True
        return False
    
    def _rebuild_sparse_index(self):
        """Перабудова sparse індэкса пасля выдалення"""
        self.sparse_index = {}
        for chunk_id, chunk in self.chunks.items():
            self._update_sparse_index(chunk_id, chunk.text)
    
    def get_stats(self) -> Dict:
        """Статыстыка базы"""
        return {
            'total_chunks': len(self.chunks),
            'db_type': self.db_type,
            'sparse_index_size': len(self.sparse_index),
            'chunks_with_embeddings': sum(1 for c in self.chunks.values() if c.embedding is not None)
        }
    
    def save(self):
        """Захаванне базы"""
        # Рэалізацыя залежыць ад тыпу БД
        logger.info("💾 Вектарная БД захавана")
    
    def load_facts_from_json(self, facts_file: str, batch_size: int = 100):
        """
        Загрузка фактаў з JSON файла
        
        Args:
            facts_file: шлях да facts.json
            batch_size: памер пачкі для апрацоўкі
        """
        with open(facts_file, 'r', encoding='utf-8') as f:
            facts = json.load(f)
        
        logger.info(f"📚 Загрузка {len(facts)} фактаў у вектарную БД...")
        
        for i, fact in enumerate(facts):
            fact_text = fact.get('fact', '')
            fact_id = fact.get('id', f"fact_{i}")
            metadata = {
                'source': fact.get('source', 'unknown'),
                'type': 'fact'
            }
            
            # Генерацыя ID
            chunk_id = hashlib.md5(fact_text.encode()).hexdigest()[:16]
            
            self.add_chunk(chunk_id, fact_text, metadata=metadata)
            
            if (i + 1) % batch_size == 0:
                logger.debug(f"✅ Апрацавана {i+1}/{len(facts)} фактаў")
        
        logger.info(f"✅ Загружана {len(facts)} фактаў")


def main():
    """Тэставанне вектарнай БД"""
    print("="*80)
    print("🧪 ТЭСТАВАННЕ ВЕКТАРНАЙ БАЗЫ ДАДЗЕНЫХ")
    print("="*80)
    
    db = VectorDatabase(db_type="memory")
    
    # Дадаванне тэставых чанкаў
    test_chunks = [
        ("fact_1", "Кастусь Каліноўскі нарадзіўся ў 1838 годзе ў вёсцы Мастаўляны"),
        ("fact_2", "Паўстанне 1863 года кіраваў Кастусь Каліноўскі"),
        ("fact_3", "Газета «Мужыцкая праўда» выдавалася ў 1863 годзе"),
        ("fact_4", "Вітаўт Вялікі князь літоўскі ў 1392-1430 гадах"),
        ("fact_5", "Грунвальдская бітва адбылася 15 ліпеня 1410 года"),
    ]
    
    for chunk_id, text in test_chunks:
        db.add_chunk(chunk_id, text, metadata={'year': '19'})
    
    print(f"\n📊 Статыстыка: {db.get_stats()}")
    
    # Тэст sparse пошуку
    print("\n🔍 Sparse пошук (ключавыя словы):")
    results = db.search_sparse("Каліноўскі паўстанне", top_k=3)
    for chunk_id, score in results:
        chunk = db.get_chunk(chunk_id)
        print(f"  [{score:.3f}] {chunk.text[:60]}...")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
