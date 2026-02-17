#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 ТЭСТАВАННЕ СІСТЭМЫ
"""

import json
import time
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))

from src.core.ultimate_engine_v1 import BelarusUltimateEngine
from src.core.logger import logger


class MetricsTester:
    """Тэставанне з метрыкамі"""

    def __init__(self):
        print("🔄 Ініцыялізацыя рухавіка...")
        self.engine = BelarusUltimateEngine()

        # "Залаты стандарт" — 20 пытанняў
        self.gold_standard = [
            {'question': 'Хто такі Кастусь Каліноўскі?', 'expected': ['каліноўскі', 'паўстанне', '1863'], 'category': 'асобы'},
            {'question': 'Калі быў створаны Статут 1588?', 'expected': ['статут', '1588', 'вкл'], 'category': 'дакументы'},
            {'question': 'Што такое Вялікае Княства Літоўскае?', 'expected': ['вялікае', 'княства', 'літоўскае'], 'category': 'дзяржавы'},
            {'question': 'Гісторыя Полацка', 'expected': ['полацк', 'княства'], 'category': 'гарады'},
            {'question': 'Вайна 1812 года ў Беларусі', 'expected': ['1812', 'вайна', 'напалеон'], 'category': 'войны'},
            {'question': 'Хто такі Францыск Скарына?', 'expected': ['скарына', 'кніга', 'друкар'], 'category': 'асобы'},
            {'question': 'Што такое Люблінская унія?', 'expected': ['люблінская', 'унія', '1569'], 'category': 'падзеі'},
            {'question': 'Грунвальдская бітва 1410 года', 'expected': ['грунвальдская', 'бітва', '1410'], 'category': 'войны'},
            {'question': 'Хто такі Леў Сапега?', 'expected': ['сапега', 'канцлер', 'статут'], 'category': 'асобы'},
            {'question': 'Што такое Брэсцкая унія?', 'expected': ['брэсцкая', 'унія', '1596'], 'category': 'падзеі'},
            {'question': 'Гісторыя Мінска', 'expected': ['мінск', 'горад'], 'category': 'гарады'},
            {'question': 'Паўстанне 1863-1864 гадоў', 'expected': ['паўстанне', '1863', 'каліноўскі'], 'category': 'падзеі'},
            {'question': 'Хто такі Вітаўт?', 'expected': ['вітаўт', 'князь', 'вкл'], 'category': 'асобы'},
            {'question': 'Што такое Статут ВКЛ 1529 года?', 'expected': ['статут', '1529', 'вкл'], 'category': 'дакументы'},
            {'question': 'Ягайла і Крэўская унія', 'expected': ['ягайла', 'крэўская', 'унія'], 'category': 'падзеі'},
            {'question': 'Хто такі Міхал Клеафас Агінскі?', 'expected': ['агінскі', 'кампазітар'], 'category': 'асобы'},
            {'question': 'Што такое Тэўтонскі ордэн?', 'expected': ['тэўтонскі', 'ордэн', 'крыжакі'], 'category': 'арганізацыі'},
            {'question': 'Вялікая Айчынная вайна 1941-1945', 'expected': ['вайна', '1941', '1945'], 'category': 'войны'},
            {'question': 'Хто такі Янка Купала?', 'expected': ['купала', 'паэт'], 'category': 'асобы'},
            {'question': 'Што такое БНР?', 'expected': ['бнр'], 'category': 'дзяржавы'},
        ]

    def calculate_metrics(self, found_text, expected_keywords):
        """Разлік дакладнасці і паўнаты"""
        found_lower = found_text.lower()
        
        # Колькі знойдзена з чаканых
        found_keywords = [kw for kw in expected_keywords if kw in found_lower]
        found_count = len(found_keywords)
        total_expected = len(expected_keywords)
        
        # Recall: доля знойдзеных чаканых слоў
        recall = found_count / total_expected if total_expected > 0 else 0
        
        # Precision: бінарная — ці знойдзена хоць бы 1 слова
        precision = 1.0 if found_count > 0 else 0.0
        
        # F1
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0
            
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'found_count': found_count,
            'total_expected': total_expected,
            'found_keywords': found_keywords
        }

    def run_tests(self):
        """Запуск тэстаў"""
        print("="*80)
        print("📊 ТЭСТАВАННЕ СІСТЭМЫ")
        print("="*80)

        total_precision = 0
        total_recall = 0
        total_f1 = 0
        response_times = []
        passed = 0

        for i, test in enumerate(self.gold_standard, 1):
            # Замер часу
            start = time.time()
            answer = self.engine.answer_formatted(test['question'])
            elapsed = (time.time() - start) * 1000
            response_times.append(elapsed)

            # Разлік метрык
            metrics = self.calculate_metrics(answer, test['expected'])

            total_precision += metrics['precision']
            total_recall += metrics['recall']
            total_f1 += metrics['f1']

            if metrics['recall'] >= 0.5:
                passed += 1
                status = "✅"
            else:
                status = "❌"

            if i <= 5 or i % 5 == 0:
                print(f"  {status} Тэст {i}: {test['question'][:40]}")
                print(f"      Recall={metrics['recall']:.0%}, Знойдзена: {metrics['found_keywords']}")

        # Сярэднія значэнні
        n = len(self.gold_standard)
        results = {
            'precision': total_precision / n,
            'recall': total_recall / n,
            'f1': total_f1 / n,
            'avg_response_time_ms': sum(response_times) / n,
            'passed': passed,
            'total': n
        }

        # Вынікі
        print("\n" + "="*80)
        print("📊 ВЫНІКОВЫЯ МЕТРЫКІ")
        print("="*80)
        print(f"   Precision (дакладнасць): {results['precision']:.2%}")
        print(f"   Recall (паўната):         {results['recall']:.2%}")
        print(f"   F1-score:                 {results['f1']:.2%}")
        print(f"   Час адказу:               {results['avg_response_time_ms']:.2f} мс")
        print(f"   Пройдзена тэстаў:         {results['passed']}/{results['total']}")

        # Захоўваем вынікі
        results_file = Path("tests/metrics_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n📁 Вынікі захаваны: {results_file}")

        # Рэкамендацыя
        print("\n" + "="*80)
        if results['recall'] >= 0.5:
            print(f"✅ GOOD! Recall {results['recall']:.0%} >= 50%")
        else:
            print(f"⚠️  Трэба паляпшаць. Recall {results['recall']:.0%} < 50%")
        print("="*80)

        return results


def main():
    tester = MetricsTester()
    tester.run_tests()


if __name__ == "__main__":
    main()
