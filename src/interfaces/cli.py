#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Консольный интерфейс для БелЭталон-2.
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.engine import BelarusEtalonEngine

def print_header():
    print("="*80)
    print("🧠 БЕЛЭТАЛОН-2 — ІНТЭЛЕКТУАЛЬНЫ ПОШУК")
    print("="*80)
    print("📚 Крыніцы: падручнікі гісторыі + Беларуская энцыклапедыя (18 тамоў)")
    print(f"📊 Загружана эталонаў: ?")
    print()

def print_examples():
    print("💡 Прыклады пытанняў:")
    examples = [
        "Хто такі Кастусь Каліноўскі?",
        "Што такое Вялікае Княства Літоўскае?",
        "Калі было паўстанне 1863 года?",
        "Хто заснаваў Полацк?",
        "Што такое Статут ВКЛ?",
        "Калі адбылася Грунвальдская бітва?",
        "Хто такі Францыск Скарына?"
    ]
    for ex in examples:
        print(f"   • {ex}")
    print("\n   Каб выйсці, увядзіце 'выйсці' або націсніце Ctrl+C\n")

def main():
    print_header()
    
    # Инициализируем движок
    engine = BelarusEtalonEngine()
    
    if not engine.facts:
        print("\n❌ Памылка: няма загружаных эталонаў!")
        print("💡 Запусціце спачатку будаўніка:")
        print("   python3 src/builders/build_fact_etalons.py")
        return
    
    print_examples()
    
    while True:
        try:
            q = input("❓ Пытанне: ").strip()
            if q.lower() in ['выйсці', 'exit', 'quit', '']:
                print("\nДа пабачэння! 👋")
                break
            
            if not q:
                continue
            
            print("\n" + "="*80)
            print(engine.answer_simple(q))
            print("="*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nДа пабачэння! 👋")
            break
        except Exception as e:
            print(f"\n❌ Памылка: {e}\n")

if __name__ == "__main__":
    main()
