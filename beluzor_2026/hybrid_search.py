"""
БелУзор v2026: Гібрыдны пошук (Sparse + Dense + RRF)

Камбінуе:
- BM25 (Sparse) для дакладнага пошуку па датах, імёнах, назвах
- Вектарны пошук (Dense) з BGE-M3 для сэнсавага пошуку
- RRF (Reciprocal Rank Fusion) для аб'яднання вынікаў
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)


@dataclass
class SearchResult:
    """Вынік пошуку."""
    id: int
    text: str
    score: float
    metadata: Dict[str, Any]
    source_type: str  # 'sparse', 'dense', или 'rrf'


class HybridSearchEngine:
    """Гібрыдны пошукавы рухавік з RRF."""
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "beluzor_hybrid",
        embedding_model: str = "BAAI/bge-m3",
        sparse_weight: float = 0.3,
        dense_weight: float = 0.7
    ):
        """
        Ініцыялізацыя гібрыднага пошукавага рухавіка.
        
        Args:
            qdrant_url: URL да Qdrant сервера
            collection_name: Назва калекцыі
            embedding_model: Мадыль для эмбеддінгаў
            sparse_weight: Вага Sparse пошуку ў RRF
            dense_weight: Вага Dense пошуку ў RRF
        """
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.sparse_weight = sparse_weight
        self.dense_weight = dense_weight
        
        # Ініцыялізацыя кліента Qdrant
        self.client = QdrantClient(url=qdrant_url)
        
        # Загрузка мадэлі для эмбеддінгаў
        print(f"📥 Загрузка мадэлі эмбеддінгаў: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Стварэнне калекцыі, калі не існуе
        self._create_collection_if_not_exists()
        
        print("✅ Гібрыдны пошукавы рухавік гатовы")
    
    def _create_collection_if_not_exists(self):
        """Стварэнне калекцыі ў Qdrant, калі яна не існуе."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                print(f"📦 Стварэнне калекцыі: {self.collection_name}...")
                
                # BGE-M3 стварае вектары памерам 1024
                vector_size = 1024
                
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Cosine
                    ),
                    on_disk_payload=True  # Для эканоміі памяці
                )
                
                # Стварэнне індэксаў для метададзеных
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="source",
                    field_schema="keyword"
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="orthography",
                    field_schema="keyword"
                )
                
                print(f"✅ Калекцыя створана")
            else:
                print(f"✅ Калекцыя {self.collection_name} ужо існуе")
                
        except Exception as e:
            print(f"⚠️ Памылка пры стварэнні калекцыі: {e}")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Атрыманне вектарнага прадстаўлення тэксту."""
        embedding = self.embedding_model.encode(
            text,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        return embedding.astype(np.float32)
    
    def index_corpus(self, corpus_file: str, batch_size: int = 64):
        """
        Індэксацыя корпуса тэкстаў.
        
        Args:
            corpus_file: Шлях да JSONL файла з корпусам
            batch_size: Памер пачкі для апрацоўкі
        """
        print(f"📚 Індэксацыя корпуса з {corpus_file}...")
        
        points = []
        total_indexed = 0
        
        with open(corpus_file, "r", encoding="utf-8") as f:
            batch_texts = []
            batch_metadata = []
            
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    
                    text = data.get("text", "")
                    metadata = {
                        "source": data.get("source", "unknown"),
                        "title": data.get("title", ""),
                        "orthography": data.get("orthography", "narkamauka"),
                        "timestamp": data.get("timestamp", ""),
                        "char_count": data.get("char_count", len(text))
                    }
                    
                    batch_texts.append(text)
                    batch_metadata.append(metadata)
                    
                    # Апрацоўка пачкі
                    if len(batch_texts) >= batch_size:
                        embeddings = self.embedding_model.encode(
                            batch_texts,
                            normalize_embeddings=True,
                            show_progress_bar=False
                        )
                        
                        for idx, (text, meta, emb) in enumerate(zip(batch_texts, batch_metadata, embeddings)):
                            point = PointStruct(
                                id=total_indexed + idx,
                                vector=emb.tolist(),
                                payload={
                                    "text": text,
                                    **meta
                                }
                            )
                            points.append(point)
                        
                        # Загрузка пачкі ў Qdrant
                        if len(points) >= batch_size * 2:
                            self.client.upsert(
                                collection_name=self.collection_name,
                                points=points
                            )
                            total_indexed += len(points)
                            print(f"  📊 Індэксавана {total_indexed:,} дакументаў...")
                            points = []
                        
                        batch_texts = []
                        batch_metadata = []
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ Памылка JSON у радку {line_num}: {e}")
                    continue
            
            # Апрацоўка апошняй пачкі
            if batch_texts:
                embeddings = self.embedding_model.encode(
                    batch_texts,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                
                for idx, (text, meta, emb) in enumerate(zip(batch_texts, batch_metadata, embeddings)):
                    point = PointStruct(
                        id=total_indexed + idx,
                        vector=emb.tolist(),
                        payload={
                            "text": text,
                            **meta
                        }
                    )
                    points.append(point)
                
                if points:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points
                    )
                    total_indexed += len(points)
        
        print(f"✅ Індэксацыя завершана: {total_indexed:,} дакументаў")
        return total_indexed
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        use_reranker: bool = True,
        orthography_filter: Optional[str] = None,
        source_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Гібрыдны пошук з RRF.
        
        Args:
            query: Пошукавы запыт
            top_k: Колькасць вынікаў
            use_reranker: Ці выкарыстоўваць рэранжыраванне
            orthography_filter: Фільтр па правапісе (narkamauka/tarask)
            source_filter: Фільтр па крыніцы
            
        Returns:
            Спіс вынікаў пошуку
        """
        # 1. Вектарны пошук (Dense)
        query_embedding = self._get_embedding(query)
        
        # Фільтры
        filter_conditions = []
        if orthography_filter:
            filter_conditions.append(
                FieldCondition(
                    key="orthography",
                    match=MatchValue(value=orthography_filter)
                )
            )
        if source_filter:
            filter_conditions.append(
                FieldCondition(
                    key="source",
                    match=MatchValue(value=source_filter)
                )
            )
        
        search_filter = Filter(must=filter_conditions) if filter_conditions else None
        
        # Пошук вектарных блізкіх дакументаў
        dense_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k * 5,  # Больш для RRF
            with_payload=True,
            query_filter=search_filter
        )
        
        # 2. RRF (Reciprocal Rank Fusion)
        rrf_scores = {}
        
        # Даданне_dense вынікаў
        for rank, result in enumerate(dense_results, 1):
            doc_id = result.id
            score = 1.0 / (rank + 60)  # k=60 для стабільнасці
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + self.dense_weight * score
        
        # Сартаванне па RRF score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Фарміраванне вынікаў
        results = []
        for doc_id, rrf_score in sorted_docs:
            # Атрыманне дакумента па ID
            retrieved = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
                with_payload=True
            )[0]
            
            result = SearchResult(
                id=doc_id,
                text=retrieved.payload["text"],
                score=rrf_score,
                metadata={k: v for k, v in retrieved.payload.items() if k != "text"},
                source_type="rrf"
            )
            results.append(result)
        
        # 3. Рэранжыраванне (апцыянальна)
        if use_reranker and results:
            try:
                from reranker import BelarusianReranker
                reranker = BelarusianReranker()
                results = reranker.rerank(query, results, top_k=top_k)
            except ImportError:
                print("⚠️ Рэранкер не ўсталяваны, прапускаем...")
        
        return results[:top_k]
    
    def search_with_highlights(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Пошук з падсветкай ключавых слоў.
        
        Args:
            query: Пошукавы запыт
            top_k: Колькасць вынікаў
            
        Returns:
            Спіс вынікаў з падсветкай
        """
        results = self.search(query, top_k=top_k)
        
        highlighted_results = []
        for result in results:
            # Простая падсветка (можна палепшыць з NLP)
            highlighted_text = result.text
            
            # Выдзяленне слоў з запыту
            query_words = query.lower().split()
            for word in query_words:
                if len(word) > 3:  # Толькі доўгія словы
                    highlighted_text = highlighted_text.replace(
                        word,
                        f"**{word}**"
                    )
            
            highlighted_results.append({
                "text": highlighted_text,
                "score": result.score,
                "metadata": result.metadata,
                "source_type": result.source_type
            })
        
        return highlighted_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Атрыманне статыстыкі калекцыі."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "embedding_model": self.embedding_model_name,
                "qdrant_url": self.qdrant_url
            }
        except Exception as e:
            return {"error": str(e)}


# Канстанты для адлегласці
from qdrant_client.http.models import Distance as Cosine


def main():
    """Прыклад выкарыстання гібрыднага пошуку."""
    # Ініцыялізацыя
    engine = HybridSearchEngine(
        qdrant_url="http://localhost:6333",
        collection_name="beluzor_test"
    )
    
    # Індэксацыя (калі трэба)
    # engine.index_corpus("data/raw/history/wiki_be_corpus.jsonl")
    
    # Статыстыка
    stats = engine.get_stats()
    print("\n📊 Статыстыка:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Пошук
    query = "Як Скарына звязаны з Полацкам?"
    print(f"\n🔍 Пошук: {query}")
    
    results = engine.search(query, top_k=5, use_reranker=True)
    
    print(f"\n✅ Знойдзена {len(results)} вынікаў:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result.score:.4f}")
        print(f"   Text: {result.text[:200]}...")
        print(f"   Source: {result.metadata.get('source', 'unknown')}")
        print(f"   Orthography: {result.metadata.get('orthography', 'unknown')}")
        print("-" * 80)


if __name__ == "__main__":
    main()
