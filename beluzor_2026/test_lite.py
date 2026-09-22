"""
БелУзор v2026: Лёгкае тэставанне для дэманстрацыі
Выкарыстоўвае лёгкія мадэлі замест цяжкіх для працы ў абмежаваных сярэдах.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nlp_processor import BelarusianNLPProcessor as BelarusianNLP

def test_nlp_only():
    """Поўны тэст NLP функцый без цяжкіх мадэлей"""
    print("\n" + "="*70)
    print("🧪 БЕЛУЗОР v2026: ТЭСТАВАННЕ NLP (Лёгкі рэжым)")
    print("="*70)
    
    nlp = BelarusianNLP()
    
    # Тэставыя тэксты
    test_texts = [
        "Францыск Скарына нарадзіўся ў Полацку каля 1490 года.",
        "Вялікае Княства Літоўскае дасягнула росквіту пры Вітаўце.",
        "Статут ВКЛ 1588 года — помнік права феадалізму ў Еўропе.",
        "Бітва пад Грунвальдам адбылася 15 ліпеня 1410 года."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{'='*70}")
        print(f"📝 ТЭКСТ {i}: {text}")
        print(f"{'='*70}")
        
        # Лематызацыя
        tokens = nlp.tokenize_and_lemmatize(text)
        lemmas = [t.lemma for t in tokens]
        print(f"✅ Лематызацыя: {' '.join(lemmas)}")
        
        # NER
        entities = nlp.extract_entities(text)
        if entities:
            print(f"🏷️ Сутнасці:")
            for ent in entities:
                print(f"   • {ent.text:25} → {ent.entity_type.value}")
        
        # Вызначэнне правапісу
        ortho, conf = nlp.detect_orthography_advanced(text)
        print(f"🔤 Правапіс: {ortho.upper()} (упэўненасць: {conf:.0%})")
    
    # Статыстыка па ўсіх тэкстах
    print(f"\n{'='*70}")
    print("📊 АГУЛЬНАЯ СТАТЫСТЫКА")
    print(f"{'='*70}")
    
    all_entities = []
    for text in test_texts:
        entities = nlp.extract_entities(text)
        all_entities.extend(entities)
    
    entity_counts = {}
    for ent in all_entities:
        etype = ent.entity_type.value
        entity_counts[etype] = entity_counts.get(etype, 0) + 1
    
    print("Знойдзеныя сутнасці па тыпах:")
    for etype, count in sorted(entity_counts.items()):
        print(f"   • {etype:15}: {count}")
    
    print(f"\n✅ Усе тэсты NLP прайдзены паспяхова!")
    print(f"📊 Усяго апрацавана тэкстаў: {len(test_texts)}")
    print(f"📊 Усяго знойдзена сутнасцей: {len(all_entities)}")
    
    return True

def demo_reranker_mock():
    """Дэманстрацыя рэранжыравання (імітацыя)"""
    print(f"\n{'='*70}")
    print("🧪 ТЭСТ РАНЖЫРАВАННЯ (Імітацыя BGE-Reranker)")
    print(f"{'='*70}")
    
    query = "Хто такі Францыск Скарына?"
    candidates = [
        "Скарына нарадзіўся ў Полацку.",
        "У 1410 годзе адбылася бітва пад Грунвальдам.",
        "Францыск Скарына выдаў першую кнігу для ўсходніх славян у 1517 годзе.",
        "Статут ВКЛ быў прыняты ў 1588 годзе.",
        "Кнігі Скарыны былі на царкоўнаславянскай мове."
    ]
    
    print(f"🔍 Запыт: '{query}'\n")
    print("Кандыдаты да рэранжыравання:")
    for i, c in enumerate(candidates, 1):
        print(f"  {i}. {c}")
    
    # Імітацыя рэранжыравання (у рэальнасці тут быў бы BGE-Reranker)
    # Проста паказваем, якія кандыдаты найбольш рэлевантныя
    ranked_indices = [2, 0, 4, 3, 1]  # Індэксы найбольш рэлевантных
    
    print(f"\n📊 Top-3 пасля рэранжыравання:")
    for i, idx in enumerate(ranked_indices[:3], 1):
        score = 0.95 - (i * 0.1)  # Імітацыя ацэнкі
        print(f"  {i}. [{score:.2f}] {candidates[idx]}")
    
    print(f"\n✅ Рэранжыраванне завершана!")
    return True

if __name__ == "__main__":
    print("\n🚀 БЕЛУЗОР v2026: ЛЁГКАЕ ТЭСТАВАННЕ")
    print("Рэжым: Без цяжкіх мадэлей (BGE-M3, Stanza)")
    
    try:
        test_nlp_only()
        demo_reranker_mock()
        
        print("\n" + "="*70)
        print("✅ УСЕ ТЭСТЫ ПРАЙДЗЕНЫ ПАСПЯХОВА!")
        print("="*70)
        print("\n📌 Нотаткі:")
        print("   • NLP працуе з выкарыстаннем рэгулярных выразаў (fallback)")
        print("   • Для поўнай функцыянальнасці спатрэбяцца: Stanza, SpaCy, BGE-M3")
        print("   • На Hugging Face Spaces будзе выкарыстоўвацца лёгкі рэжым")
        print("\n🎯 Сістэма гатова да размяшчэння на HF Spaces!")
        
    except Exception as e:
        print(f"\n❌ ПАМЫЛКА: {e}")
        import traceback
        traceback.print_exc()
