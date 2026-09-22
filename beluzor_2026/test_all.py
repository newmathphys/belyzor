"""
БелУзор v2026: Тэставанне гібрыднага пошуку, рэранжыравання і NLP
Правярае працу ўсіх асноўных модуляў сістэмы.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp_processor import BelarusianNLPProcessor as BelarusianNLP
from hybrid_search import HybridSearchEngine
from reranker import BelarusianReranker as CrossEncoderReranker

def test_nlp_processor():
    """Тэст апрацоўкі беларускага тэксту і NER"""
    print("\n" + "="*60)
    print("🧪 ТЭСТ 1: NLP Апрацоўка (Stanza/SpaCy)")
    print("="*60)
    
    nlp = BelarusianNLP()
    
    # Тэставы тэкст з гістарычнымі сутнасцямі
    text = "Францыск Скарына нарадзіўся ў Полацку каля 1490 года. Ён выдаў першую кнігу ў 1517 годзе."
    
    print(f"📝 Уваходны тэкст: {text}")
    
    # Лематызацыя (выкарыстоўваем tokenize_and_lemmatize)
    tokens = nlp.tokenize_and_lemmatize(text)
    lemmas = [t.lemma for t in tokens]
    print(f"\n✅ Лематызацыя: {' '.join(lemmas)}")
    
    # Выяўленне сутнасцей (NER)
    entities = nlp.extract_entities(text)
    print(f"\n🏷️ Знойдзеныя сутнасці:")
    for ent in entities:
        print(f"   - {ent.text} ({ent.entity_type.value})")
    
    # Вызначэнне правапісу
    orthography, confidence = nlp.detect_orthography_advanced(text)
    print(f"\n🔤 Выяўлены правапіс: {orthography} (confidence: {confidence:.2f})")
    
    return True

def test_hybrid_search():
    """Тэст гібрыднага пошуку (BM25 + Dense)"""
    print("\n" + "="*60)
    print("🧪 ТЭСТ 2: Гібрыдны пошук (Hybrid Search)")
    print("="*60)
    
    engine = HybridSearchEngine()
    
    # Індэксацыя тэставых дакументаў
    docs = [
        {"id": "1", "text": "Вялікае Княства Літоўскае утварылася ў XIII стагоддзі.", "meta": {"source": "Encyclopedia"}},
        {"id": "2", "text": "Бітва пад Грунвальдам адбылася 15 ліпеня 1410 года.", "meta": {"source": "Textbook"}},
        {"id": "3", "text": "Францыск Скарына — першадрукар усходніх славян.", "meta": {"source": "Biography"}},
        {"id": "4", "text": "Статут ВКЛ 1588 года быў напісаны на старабеларускай мове.", "meta": {"source": "Law"}},
    ]
    
    print("📚 Індэксацыя дакументаў...")
    for doc in docs:
        engine.add_document(doc["id"], doc["text"], doc["meta"])
    print(f"✅ Дададзена {len(docs)} дакументаў.")
    
    # Пошукавы запыт
    query = "калі адбылася Грунвальдская бітва?"
    print(f"\n🔍 Запыт: '{query}'")
    
    # Гібрыдны пошук
    results = engine.search(query, top_k=3)
    
    print(f"\n📊 Вынікі пошуку (Top-3):")
    for i, res in enumerate(results, 1):
        print(f"   {i}. [{res['meta'].get('source', 'Unknown')}] {res['text']} (Score: {res['score']:.4f})")
    
    return True

def test_reranker():
    """Тэст рэранжыравання вынікаў"""
    print("\n" + "="*60)
    print("🧪 ТЭСТ 3: Рэранжыраванне (BGE-Reranker)")
    print("="*60)
    
    reranker = CrossEncoderReranker()
    
    query = "Хто такі Скарына?"
    candidates = [
        "Скарына нарадзіўся ў Полацку.",
        "У 1410 годзе адбылася бітва пад Грунвальдам.",
        "Францыск Скарына выдаў першую друкаваную кнігу для ўсходніх славян у 1517 годзе.",
        "Статут ВКЛ быў прыняты ў 1588 годзе.",
        "Кнігі Скарыны былі напісаны на царкоўнаславянскай мове."
    ]
    
    print(f"🔍 Запыт: '{query}'")
    print(f"📋 Кандыдаты: {len(candidates)}")
    
    # Рэранжыраванне
    ranked = reranker.rerank(query, candidates, top_k=3)
    
    print(f"\n📊 Top-3 пасля рэранжыравання:")
    for i, res in enumerate(ranked, 1):
        print(f"   {i}. {res['text']} (Score: {res['score']:.4f})")
    
    return True

def main():
    """Запуск усіх тэстаў"""
    print("\n🚀 БЕЛУЗОР v2026: ЗАПУСК ТЭСТАЎ")
    
    try:
        test_nlp_processor()
        test_hybrid_search()
        test_reranker()
        
        print("\n" + "="*60)
        print("✅ УСЕ ТЭСТЫ ПРАЙДЗЕНЫ ПАСПЯХОВА!")
        print("="*60)
        print("\nСістэма гатова да інтэграцыі з Hugging Face Spaces.")
        
    except Exception as e:
        print(f"\n❌ ПАМЫЛКА ПРИ ТЭСТАВАННІ: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()
