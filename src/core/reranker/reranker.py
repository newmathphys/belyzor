#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 БЕЛУЗОР v2026 — Рэранжыраванне фактаў з BGE-Reranker / Cross-Encoder

Падтрымка:
- BAAI/bge-reranker-v2-m3 (лепшы для славянскіх моў)
- Cross-encoder мадэлі
- Інтэграцыя з RAG працэсам
"""

import numpy as np
from typing import List, Tuple, Dict
from pathlib import Path

from src.core.logger import logger


class Reranker:
    """
    Рэранжыраванне пошукавых вынікаў
    
    Выкарыстоўвае cross-encoder мадэлі для дакладнай ацэнкі рэлевантнасці
    """
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", 
                 device: str = "cpu",
                 top_k: int = 5):
        """
        Ініцыялізацыя рэранжыравальніка
        
        Args:
            model_name: назва мадэлі з HuggingFace
            device: "cpu" ці "cuda"
            top_k: колькасць лепшых вынікаў пасля рэранжыравання
        """
        self.model_name = model_name
        self.device = device
        self.top_k = top_k
        
        self.model = None
        self.tokenizer = None
        
        # Загрузка мадэлі
        self._load_model()
    
    def _load_model(self):
        """Загрузка мадэлі з HuggingFace"""
        try:
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            
            logger.info(f"📥 Загрузка рэранжыравальніка: {self.model_name}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            if self.device == "cuda":
                self.model = self.model.to("cuda")
            
            self.model.eval()
            logger.info(f"✅ Рэранжыравальнік загружаны на {self.device}")
            
        except ImportError:
            logger.warning("⚠️ transformers не усталяваны. Выкарыстоўвайце заглушку.")
            self.model = None
        except Exception as e:
            logger.error(f"❌ Памылка загрузкі рэранжыравальніка: {e}")
            self.model = None
    
    def rerank(self, query: str, documents: List[str], 
               return_scores: bool = True) -> List[Tuple[str, float]]:
        """
        Рэранжыраванне дакументаў па запыце
        
        Args:
            query: пошукавы запыт
            documents: спіс дакументаў для рэранжыравання
            return_scores: ці вяртаць ацэнкі
            
        Returns:
            Спіс (дакумент, score) адсартаваны па рэлевантнасці
        """
        if not documents:
            return []
        
        if self.model is None:
            # Заглушка - проста вяртаем як ёсць
            return [(doc, 1.0) for doc in documents[:self.top_k]]
        
        # Стварэнне пар (query, document) для cross-encoder
        pairs = [[query, doc] for doc in documents]
        
        # Ацэнка рэлевантнасці
        scores = self._compute_scores(pairs)
        
        # Сартыроўка
        ranked = list(zip(documents, scores))
        ranked.sort(key=lambda x: -x[1])
        
        # Вяртанне top_k
        if return_scores:
            return ranked[:self.top_k]
        else:
            return [doc for doc, score in ranked[:self.top_k]]
    
    def _compute_scores(self, pairs: List[List[str]]) -> List[float]:
        """Вылічэнне ацэнак для пар запыт-дакумент"""
        scores = []
        
        batch_size = 8
        for i in range(0, len(pairs), batch_size):
            batch_pairs = pairs[i:i+batch_size]
            
            # Токенізацыя
            encoded = self.tokenizer(
                batch_pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            if self.device == "cuda":
                encoded = {k: v.to("cuda") for k, v in encoded.items()}
            
            # Атрыманне ацэнак
            with np.errstate(divide='ignore', invalid='ignore'):
                with __import__('torch').no_grad():
                    outputs = self.model(**encoded)
                    batch_scores = outputs.logits.cpu().numpy().flatten()
                    scores.extend(batch_scores.tolist())
        
        # Нармалізацыя ў дыяпазон [0, 1]
        if scores:
            min_score = min(scores)
            max_score = max(scores)
            if max_score > min_score:
                scores = [(s - min_score) / (max_score - min_score) for s in scores]
            else:
                scores = [1.0] * len(scores)
        
        return scores
    
    def rerank_with_metadata(self, query: str, 
                            documents: List[Dict]) -> List[Tuple[Dict, float]]:
        """
        Рэранжыраванне дакументаў з метаданымі
        
        Args:
            query: пошукавы запыт
            documents: спіс dict з ключам 'text' і іншымі метаданымі
            
        Returns:
            Спіс (дакумент_з_метаданымі, score)
        """
        texts = [doc.get('text', '') for doc in documents]
        ranked_results = self.rerank(query, texts, return_scores=True)
        
        # Суаднясенне з арыгінальнымі дакументамі
        result_map = {text: score for text, score in ranked_results}
        
        ranked_docs = []
        for doc in documents:
            text = doc.get('text', '')
            if text in result_map:
                ranked_docs.append((doc, result_map[text]))
        
        ranked_docs.sort(key=lambda x: -x[1])
        return ranked_docs[:self.top_k]


class AdvancedReranker(Reranker):
    """
    Пашыраны рэранжыравальнік з некалькімі мадэлямі
    
    Выкарыстоўвае ансамбль мадэляў для лепшай дакладнасці
    """
    
    def __init__(self, model_names: List[str] = None, device: str = "cpu",
                 top_k: int = 5, ensemble_strategy: str = "average"):
        """
        Ініцыялізацыя ансамбля рэранжыравальнікаў
        
        Args:
            model_names: спіс назваў мадэляў
            device: "cpu" ці "cuda"
            top_k: колькасць лепшых вынікаў
            ensemble_strategy: "average", "weighted", "vote"
        """
        super().__init__(model_names[0] if model_names else "BAAI/bge-reranker-v2-m3", 
                        device, top_k)
        
        self.model_names = model_names or ["BAAI/bge-reranker-v2-m3"]
        self.ensemble_strategy = ensemble_strategy
        
        # Загрузка некалькіх мадэляў
        self.models = {}
        self.tokenizers = {}
        
        for model_name in self.model_names:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                
                logger.info(f"📥 Загрузка мадэлі: {model_name}...")
                
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
                
                if device == "cuda":
                    model = model.to("cuda")
                
                model.eval()
                
                self.models[model_name] = model
                self.tokenizers[model_name] = tokenizer
                
                logger.info(f"✅ Мадэль загружана: {model_name}")
                
            except Exception as e:
                logger.warning(f"⚠️ Не ўдалося загрузіць {model_name}: {e}")
    
    def rerank(self, query: str, documents: List[str], 
               return_scores: bool = True) -> List[Tuple[str, float]]:
        """Рэранжыраванне з выкарыстаннем ансамбля"""
        if not documents:
            return []
        
        if not self.models:
            # Калі ніводная мадэль не загружана
            return [(doc, 1.0) for doc in documents[:self.top_k]]
        
        all_scores = {}
        
        # Атрыманне ацэнак ад кожнай мадэлі
        for model_name, model in self.models.items():
            tokenizer = self.tokenizers[model_name]
            
            pairs = [[query, doc] for doc in documents]
            
            # Вылічэнне ацэнак
            scores = self._compute_scores_with_model(
                model, tokenizer, pairs, self.device
            )
            
            # Нармалізацыя
            if scores:
                min_s, max_s = min(scores), max(scores)
                if max_s > min_s:
                    scores = [(s - min_s) / (max_s - min_s) for s in scores]
            
            all_scores[model_name] = scores
        
        # Аб'яднанне ацэнак
        final_scores = self._combine_scores(all_scores, len(documents))
        
        # Сартыроўка
        ranked = list(zip(documents, final_scores))
        ranked.sort(key=lambda x: -x[1])
        
        if return_scores:
            return ranked[:self.top_k]
        else:
            return [doc for doc, score in ranked[:self.top_k]]
    
    def _compute_scores_with_model(self, model, tokenizer, pairs, device):
        """Вылічэнне ацэнак з канкрэтнай мадэллю"""
        scores = []
        batch_size = 8
        
        for i in range(0, len(pairs), batch_size):
            batch_pairs = pairs[i:i+batch_size]
            
            encoded = tokenizer(
                batch_pairs,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            if device == "cuda":
                encoded = {k: v.to("cuda") for k, v in encoded.items()}
            
            with np.errstate(divide='ignore', invalid='ignore'):
                with __import__('torch').no_grad():
                    outputs = model(**encoded)
                    batch_scores = outputs.logits.cpu().numpy().flatten()
                    scores.extend(batch_scores.tolist())
        
        return scores
    
    def _combine_scores(self, all_scores: Dict[str, List[float]], 
                       n_docs: int) -> List[float]:
        """Аб'яднанне ацэнак ад некалькіх мадэляў"""
        if not all_scores:
            return [1.0] * n_docs
        
        model_names = list(all_scores.keys())
        
        if self.ensemble_strategy == "average":
            # Сярэдняе арыфметычнае
            combined = []
            for i in range(n_docs):
                avg_score = sum(all_scores[m][i] for m in model_names if i < len(all_scores[m])) / len(model_names)
                combined.append(avg_score)
            return combined
        
        elif self.ensemble_strategy == "weighted":
            # Узважанае сярэдняе (першая мадэль важнейшая)
            weights = [1.0 / (i + 1) for i in range(len(model_names))]
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            combined = []
            for i in range(n_docs):
                weighted_sum = sum(
                    all_scores[m][i] * w 
                    for m, w in zip(model_names, weights) 
                    if i < len(all_scores[m])
                )
                combined.append(weighted_sum)
            return combined
        
        elif self.ensemble_strategy == "vote":
            # Галасаванне
            ranks = {}
            for model_name, scores in all_scores.items():
                sorted_indices = sorted(range(len(scores)), key=lambda i: -scores[i])
                for rank, idx in enumerate(sorted_indices):
                    if idx not in ranks:
                        ranks[idx] = 0
                    ranks[idx] += 1.0 / (rank + 1)
            
            return [ranks.get(i, 0.0) for i in range(n_docs)]
        
        else:
            # Па змаўчанні - average
            return self._combine_scores(all_scores, n_docs)


def main():
    """Тэставанне рэранжыравальніка"""
    print("="*80)
    print("🧪 ТЭСТАВАННЕ РЭРАНЖЫРАВАЛЬНІКА")
    print("="*80)
    
    # Ініцыялізацыя
    reranker = Reranker(model_name="BAAI/bge-reranker-v2-m3")
    
    # Тэставыя дадзеныя
    query = "Калі нарадзіўся Кастусь Каліноўскі?"
    
    documents = [
        "Газета «Мужыцкая праўда» выдавалася ў 1863 годзе.",
        "Кастусь Каліноўскі нарадзіўся ў 1838 годзе ў вёсцы Мастаўляны.",
        "Паўстанне 1863 года кіраваў Кастусь Каліноўскі.",
        "Вітаўт Вялікі князь літоўскі ў 1392-1430 гадах.",
        "22 сакавіка 1864 года Каліноўскага пакаралі смерцю ў Вільні.",
        "Грунвальдская бітва адбылася 15 ліпеня 1410 года.",
    ]
    
    print(f"\n🔍 Запыт: {query}")
    print(f"\n📚 Дакументы да рэранжыравання:")
    for i, doc in enumerate(documents, 1):
        print(f"  {i}. {doc[:60]}...")
    
    # Рэранжыраванне
    print("\n🔄 Рэранжыраванне...")
    ranked = reranker.rerank(query, documents, return_scores=True)
    
    print(f"\n✅ Вынікі рэранжыравання (top {reranker.top_k}):")
    for i, (doc, score) in enumerate(ranked, 1):
        print(f"  {i}. [{score:.3f}] {doc[:60]}...")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
