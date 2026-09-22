"""
БелУзор v2026: Рэранжыраванне вынікаў пошуку

Выкарыстоўвае BGE-Reranker для паляпшэння дакладнасці:
- Top-50 → Top-5 найбольш рэлевантных фактаў
- Эканомія кантэксту LLM
- Павышэнне якасці адказаў
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

try:
    from FlagEmbedding import FlagReranker
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("⚠️ FlagEmbedding не ўсталяваны. Рэранкер будзе працаваць у рэжыме імітацыі.")


@dataclass
class SearchResult:
    """Вынік пошуку (сумяшчальны з hybrid_search.py)."""
    id: int
    text: str
    score: float
    metadata: Dict[str, Any]
    source_type: str


class BelarusianReranker:
    """Рэранкер на базе BGE-Reranker для беларускіх тэкстаў."""
    
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        use_fp16: bool = True
    ):
        """
        Ініцыялізацыя рэранкера.
        
        Args:
            model_name: Назва мадэлі для рэранжыравання
            use_fp16: Выкарыстанне fp16 для паскарэння
        """
        self.model_name = model_name
        
        if RERANKER_AVAILABLE:
            print(f"📥 Загрузка рэранкера: {model_name}...")
            try:
                self.reranker = FlagReranker(
                    model_name,
                    use_fp16=use_fp16
                )
                print("✅ Рэранкер загружаны")
            except Exception as e:
                print(f"⚠️ Памылка загрузкі рэранкера: {e}")
                print("🔄 Пераход у рэжым імітацыі...")
                self.reranker = None
        else:
            print("⚠️ Рэранкер недаступны. Выкарыстоўваецца рэжым імітацыі.")
            self.reranker = None
    
    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Рэранжыраванне вынікаў пошуку.
        
        Args:
            query: Арыгінальны пошукавы запыт
            results: Спіс вынікаў для рэранжыравання
            top_k: Колькасць лепшых вынікаў
            
        Returns:
            Адсартаваны спіс лепшых вынікаў
        """
        if not results:
            return []
        
        # Калі рэранкер недаступны - вяртаем арыгінальны спіс
        if self.reranker is None:
            print("⚠️ Рэранкер у рэжыме імітацыі. Вяртаюся арыгінальны парадак.")
            return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
        
        # Падрыхтоўка пар (query, document) для рэранкера
        pairs = [(query, result.text) for result in results]
        
        # Атрыманне score ад рэранкера
        try:
            scores = self.reranker.compute_score(pairs)
            
            # Нормалізацыя score (калі трэба)
            if isinstance(scores, (list, np.ndarray)):
                scores = scores.tolist()
            else:
                # Калі вернуў адзін score для ўсіх
                scores = [scores] * len(pairs)
            
            # Даданне новых score да вынікаў
            reranked_results = []
            for result, new_score in zip(results, scores):
                # Стварэнне новай копіі з абноўленым score
                reranked_result = SearchResult(
                    id=result.id,
                    text=result.text,
                    score=float(new_score),
                    metadata=result.metadata.copy(),
                    source_type="reranked"
                )
                reranked_results.append(reranked_result)
            
            # Сартаванне па новым score
            reranked_results.sort(key=lambda x: x.score, reverse=True)
            
            print(f"📊 Рэранжыраванне: {len(results)} → {min(top_k, len(reranked_results))}")
            
            return reranked_results[:top_k]
            
        except Exception as e:
            print(f"⚠️ Памылка пры рэранжыраванні: {e}")
            # Вяртаем арыгінальны спіс у выпадку памылкі
            return sorted(results, key=lambda x: x.score, reverse=True)[:top_k]
    
    def rerank_with_explanation(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Рэранжыраванне з тлумачэннем прычын.
        
        Args:
            query: Пошукавы запыт
            results: Вынікі для рэранжыравання
            top_k: Колькасць лепшых вынікаў
            
        Returns:
            Спіс з тлумачэннямі
        """
        reranked = self.rerank(query, results, top_k=top_k * 2)  # Больш для аналізу
        
        explained_results = []
        for rank, result in enumerate(reranked[:top_k], 1):
            explanation = self._explain_relevance(query, result, rank)
            
            explained_results.append({
                "rank": rank,
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata,
                "relevance_explanation": explanation,
                "source_type": result.source_type
            })
        
        return explained_results
    
    def _explain_relevance(
        self,
        query: str,
        result: SearchResult,
        rank: int
    ) -> str:
        """
        Тлумачэнне рэлевантнасці выніку.
        
        Args:
            query: Пошукавы запыт
            result: Вынік пошуку
            rank: Пазіцыя ў рэйтынгу
            
        Returns:
            Тэкставае тлумачэнне
        """
        # Простае эврыстычнае тлумачэнне
        query_words = set(query.lower().split())
        text_words = set(result.text.lower().split())
        
        overlap = query_words & text_words
        overlap_count = len(overlap)
        
        if rank == 1:
            explanation = f"Найбольш рэлевантны вынік. Супадзенне слоў: {overlap_count}"
        elif rank <= 3:
            explanation = f"Высокая рэлевантнасць. Супадзенне слоў: {overlap_count}"
        else:
            explanation = f"Сярэдняя рэлевантнасць. Супадзенне слоў: {overlap_count}"
        
        # Дадатковыя крытэрыі
        if result.metadata.get("source") == "Wikipedia":
            explanation += " | Крыніца: Вікіпедыя (высокая надзейнасць)"
        
        if result.metadata.get("orthography") == "tarask":
            explanation += " | Тарашкевіца (гістарычны кантэкст)"
        
        return explanation
    
    def batch_rerank(
        self,
        queries: List[str],
        results_batch: List[List[SearchResult]],
        top_k: int = 5
    ) -> List[List[SearchResult]]:
        """
        Пакетнае рэранжыраванне для некалькіх запытаў.
        
        Args:
            queries: Спіс запытаў
            results_batch: Спіс спісаў вынікаў для кожнага запыту
            top_k: Колькасць лепшых вынікаў для кожнага
            
        Returns:
            Спіс пераранжыраваных вынікаў
        """
        all_reranked = []
        
        for query, results in zip(queries, results_batch):
            reranked = self.rerank(query, results, top_k=top_k)
            all_reranked.append(reranked)
        
        return all_reranked


def main():
    """Прыклад выкарыстання рэранкера."""
    # Стварэнне рэранкера
    reranker = BelarusianReranker()
    
    # Прыклад вынікаў пошуку (імітацыя)
    mock_results = [
        SearchResult(
            id=1,
            text="Францыск Скарына нарадзіўся ў Полацку каля 1490 года.",
            score=0.85,
            metadata={"source": "Wikipedia", "orthography": "narkamauka"},
            source_type="dense"
        ),
        SearchResult(
            id=2,
            text="Полацк — адзін з найстарэйшых гарадоў Беларусі, вядомы з 862 года.",
            score=0.78,
            metadata={"source": "Encyclopedia", "orthography": "narkamauka"},
            source_type="dense"
        ),
        SearchResult(
            id=3,
            text="Скарына заснаваў друкарства ва Усходняй Еўропе, выдаўшы Біблію ў 1517 годзе.",
            score=0.72,
            metadata={"source": "Textbook", "orthography": "narkamauka"},
            source_type="sparse"
        ),
        SearchResult(
            id=4,
            text="Вялікае Княства Літоўскае ўключала землі сучаснай Беларусі.",
            score=0.65,
            metadata={"source": "Wikipedia", "orthography": "tarask"},
            source_type="dense"
        ),
        SearchResult(
            id=5,
            text="Першая друкаваная кніга Скарыны была апостал, выдадзены ў Празе.",
            score=0.61,
            metadata={"source": "Book", "orthography": "narkamauka"},
            source_type="sparse"
        ),
    ]
    
    query = "Як Скарына звязаны з Полацкам?"
    
    print(f"\n🔍 Запыт: {query}\n")
    print("📋 Арыгінальныя вынікі:")
    for i, result in enumerate(mock_results, 1):
        print(f"  {i}. Score: {result.score:.3f} - {result.text[:60]}...")
    
    # Рэранжыраванне
    print("\n🔄 Рэранжыраванне...\n")
    reranked_results = reranker.rerank(query, mock_results, top_k=3)
    
    print("✅ Пасля рэранжыравання (Top-3):")
    for i, result in enumerate(reranked_results, 1):
        print(f"  {i}. Score: {result.score:.3f} - {result.text[:60]}...")
        print(f"      Source: {result.metadata['source']}, Type: {result.source_type}")
    
    # З тлумачэннямі
    print("\n📖 З тлумачэннямі:\n")
    explained = reranker.rerank_with_explanation(query, mock_results, top_k=3)
    
    for item in explained:
        print(f"  #{item['rank']}: {item['relevance_explanation']}")
        print(f"      Text: {item['text'][:80]}...\n")


if __name__ == "__main__":
    main()
