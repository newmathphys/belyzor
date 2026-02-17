#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 БЕЛЭТАЛОН v0.1
"""

import json
import re
import math
import sys
from pathlib import Path
from typing import List, Dict
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.logger import logger
from src.core.lemmatizer import BelarusianLemmatizer
from src.core.llm_interface import LLMInterface
from src.core.book_manager import BookManager


class BelarusUltimateEngine:
    """
    🚀 АСНОЎНЫЯ МАГЧЫМАСЦІ:
    1. Аўта-індэкс усіх сутнасцей з фактаў
    2. TF-IDF падобнае ранжыраванне
    3. Лематызацыя + марфалогія
    4. Пошук па частках слоў
    5. Улік частаты слоў у факце
    6. Пашыраныя асацыяцыі
    """

    def __init__(self):
        self.facts = []
        self.associations = {}
        self.entity_index = defaultdict(list)
        self.fact_tokens = []
        self.idf_scores = {}

        self.goals = {
            "гісторыя": {"value": 100, "keywords": ["вкл", "княства", "паўстанне", "статут"]},
            "гарады": {"value": 70, "keywords": ["мінск", "полацк", "віцебск", "гомель"]},
            "мову": {"value": 90, "keywords": ["граматыка", "слова", "пераклад"]},
            "культура": {"value": 60, "keywords": ["літаратура", "мастацтва", "архітэктура"]}
        }
        self.pleasure = 0

        self.stop_words = {
            'хто', 'што', 'калі', 'як', 'дзе', 'чаму', 'навошта', 'які', 'якая',
            'якое', 'якія', 'такі', 'такое', 'гэта', 'гэты', 'быў', 'была', 'было',
            'будзе', 'слова', 'азначае', 'пераклад', 'па-беларуску', 'таки',
            'з', 'і', 'або', 'та', 'каб', 'у', 'на', 'да', 'ад', 'пры', 'без',
            'мусіць', 'можа', 'трэба', 'можна', 'нельга', 'сам', 'сама', 'самі',
            'усё', 'ўсё', 'усіх', 'усім', 'тым', 'тым часам', 'як', 'бы', 'б',
            'яго', 'яе', 'іх', 'нам', 'вам', 'ім', 'мяне', 'цябе', 'нас', 'вас'
        }

        # Аўтаматычны лематызатар на аснове правілаў
        self.lemmatizer = BelarusianLemmatizer()

        # LLM інтэрфейс (апцыянальна)
        self.llm = LLMInterface()

        self.synonyms = {
            'беларусь': ['беларускія', 'беларускай', 'беларусі', 'беларуская'],
            'вялікае княства': ['вкл', 'вялікае княства літоўскае', 'літва'],
            'расія': ['масква', 'маскоўская', 'рускай', 'расійская'],
            'польшча': ['польская', 'полякі', 'польскі'],
            'літва': ['літоўская', 'літоўскае', 'літвіны'],
            'немцы': ['нямецкія', 'тэўтонскі', 'лівонскі'],
            'татары': ['татарскія', 'крымскія'],
            'швецыя': ['шведскія'],
            'францыя': ['французскія'],
            'напалеон': ['напалеона', 'напалеонам', 'французы', 'банапарт'],
            'бнр': ['беларуская народная рэспубліка', 'беларуская народная'],
            'бсср': ['беларуская савецкая'],
            'ссср': ['савецкі саюз'],
            'вкл': ['вялікае княства', 'вялікае княства літоўскае'],
            '1812': ['вайна 1812', 'айчынная вайна 1812'],
            '1941': ['вайна 1941', 'вялікая айчынная'],
            '1863': ['паўстанне 1863'],
            '1864': ['паўстанне 1864'],
            '1588': ['статут 1588'],
            '1529': ['статут 1529'],
            '1569': ['люблінская унія'],
            '1385': ['крэўская унія'],
            '1410': ['грунвальдская бітва'],
            '1596': ['брэсцкая унія'],
        }

        self.load_all()
        self.build_full_index()
        self.calculate_idf()
        logger.info("✅ Сістэма v1.0 ініцыялізавана")

    def load_all(self):
        base_path = Path(__file__).parent.parent.parent / "data/etalons"

        facts_file = base_path / "facts.json"
        if facts_file.exists():
            with open(facts_file, 'r', encoding='utf-8') as f:
                self.facts = json.load(f)
            logger.info(f"📚 Факты: {len(self.facts)}")

        for version in ['v5', 'v4', 'v3', 'v2', '']:
            assoc_file = base_path / f"associations_{version}.json" if version else base_path / "associations.json"
            if assoc_file.exists():
                with open(assoc_file, 'r', encoding='utf-8') as f:
                    self.associations = json.load(f)
                logger.info(f"🔗 Асацыяцый: {len(self.associations)}")
                break

    def tokenize(self, text):
        text_lower = text.lower()
        words = re.findall(r"[а-яёўі']+|\d{4}", text_lower)
        return [w for w in words if len(w) >= 2]

    def lemmatize(self, word):
        """Выкарыстоўвае аўтаматычны лематызатар"""
        return self.lemmatizer.lemmatize(word)

    def extract_keywords(self, text):
        tokens = self.tokenize(text)
        keywords = []
        for w in tokens:
            if w not in self.stop_words:
                lemma = self.lemmatize(w)
                if lemma not in self.stop_words:
                    keywords.append(lemma)
        return list(set(keywords))

    def expand_with_associations(self, keywords, threshold=0.08):
        expanded = set(keywords)

        for kw in keywords:
            if kw in self.synonyms:
                syn = self.synonyms[kw]
                if isinstance(syn, list):
                    expanded.update(syn)
                else:
                    expanded.add(syn)

            if kw in self.associations:
                for assoc, strength in self.associations[kw].items():
                    if strength > threshold:
                        expanded.add(assoc)

            for entity, assocs in self.associations.items():
                if kw in assocs and assocs[kw] > threshold:
                    expanded.add(entity)

        return list(expanded)

    def build_full_index(self):
        logger.info("📇 Стварэнне поўнага індэкса...")

        word_freq = defaultdict(int)
        word_to_facts = defaultdict(list)

        for i, fact in enumerate(self.facts):
            text = fact['fact'].lower()
            tokens = self.tokenize(text)

            unique_tokens = set()
            for token in tokens:
                lemma = self.lemmatize(token)
                unique_tokens.add(lemma)

            numbers = re.findall(r'\b\d{4}\b', text)
            for num in numbers:
                unique_tokens.add(num)

            abbrevs = re.findall(r'\b[А-ЯЁЎІ]{2,5}\b', fact['fact'])
            for abbr in abbrevs:
                unique_tokens.add(abbr.lower())

            for lemma in unique_tokens:
                if lemma not in self.stop_words:
                    word_freq[lemma] += 1
                    word_to_facts[lemma].append(i)

            self.fact_tokens.append(tokens)

        n_facts = len(self.facts)
        for word, freq in word_freq.items():
            if freq >= 1 and freq < n_facts * 0.5:
                self.entity_index[word] = word_to_facts[word]

        logger.info(f"✅ Індэкс гатовы: {len(self.entity_index)} слоў")

    def calculate_idf(self):
        n_docs = len(self.facts)
        for word, fact_indices in self.entity_index.items():
            df = len(fact_indices)
            self.idf_scores[word] = math.log(n_docs / (1 + df))

    def score_fact(self, fact_idx, query_keywords):
        fact_tokens = self.fact_tokens[fact_idx]
        if not fact_tokens:
            return 0.0

        tf_sum = 0.0
        for kw in query_keywords:
            count = fact_tokens.count(kw)
            if count > 0:
                tf = 1 + math.log(count) if count > 1 else 1
                idf = self.idf_scores.get(kw, 1.0)
                tf_sum += tf * idf

        norm = math.log(1 + len(fact_tokens))
        return tf_sum / norm if norm > 0 else 0.0

    def search_by_substring(self, keywords):
        results = []
        query_str = ' '.join(keywords).lower()

        for i, fact in enumerate(self.facts):
            text_lower = fact['fact'].lower()
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches >= 1:
                score = matches / len(keywords)
                results.append((i, score))

        return sorted(results, key=lambda x: -x[1])

    def answer(self, question, use_llm_ranking: bool = True):
        """
        Пошук адказаў з апцыянальным LLM рэранжыраваннем
        
        Args:
            question: Пытанне карыстальніка
            use_llm_ranking: Ці выкарыстоўваць LLM для рэранжыравання
        
        Returns:
            Спіс фактаў
        """
        try:
            keywords = self.extract_keywords(question)
            logger.info(f"🔍 Ключавыя словы: {keywords}")

            if not keywords:
                return []

            expanded = self.expand_with_associations(keywords)
            logger.info(f"🔗 Пашыраны спіс: {len(expanded)} слоў")

            fact_scores = defaultdict(float)

            for kw in expanded:
                if kw in self.entity_index:
                    for fact_idx in self.entity_index[kw]:
                        base_score = self.score_fact(fact_idx, [kw])
                        fact_scores[fact_idx] += base_score

            if len(fact_scores) < 5:
                substring_results = self.search_by_substring(keywords)
                for fact_idx, score in substring_results[:20]:
                    fact_scores[fact_idx] += score * 0.5

            # Атрыманне большага спісу для рэранжыравання
            sorted_facts = sorted(fact_scores.items(), key=lambda x: -x[1])
            
            # Калі LLM уключаны, выкарыстоўваем рэранжыраванне
            if use_llm_ranking and self.llm.enabled and len(sorted_facts) > 2:
                logger.info("🤙 LLM рэранжыраванне...")
                top_facts = [self.facts[idx]['fact'] for idx, _ in sorted_facts[:10]]
                ranked = self.llm.rank_facts(question, top_facts)
                results = [fact for fact, score in ranked[:5]]
            else:
                # Звычайнае рэранжыраванне па TF-IDF
                top_indices = [idx for idx, score in sorted_facts[:5]]
                results = [self.facts[idx]['fact'] for idx in top_indices if idx < len(self.facts)]

            self.pleasure += len(results) * 0.5
            return results

        except Exception as e:
            logger.error(f"Памылка пошуку: {e}")
            return []

    def answer_formatted(self, question, use_llm: bool = True):
        """
        Фарматаваны адказ з опцыяй LLM генерацыі
        
        Args:
            question: Пытанне карыстальніка
            use_llm: Ці выкарыстоўваць LLM для генерацыі прыгожага адказу
        """
        try:
            # Пошук фактаў
            results = self.answer(question, use_llm_ranking=use_llm)

            output = []
            output.append("="*80)
            output.append(f"📚 АДКАЗ НА ЗАПЫТ: \"{question}\"")
            output.append("="*80)
            output.append("")

            if not results:
                output.append("❌ На жаль, нічога не знойдзена па вашым запыце.")
                output.append("")
                output.append("💡 Паспрабуйце:")
                output.append("   • Змяніць фармулёўку пытання")
                output.append("   • Выкарыстоўваць больш канкрэтныя словы")
                output.append("   • Праверыць правільнасць напісання")
            else:
                # Калі LLM уключаны, генеруем прыгожы адказ
                if use_llm and self.llm.enabled:
                    llm_answer = self.llm.generate(question, results)
                    if llm_answer:
                        output.append("🤙 Адказ LLM:")
                        output.append("")
                        output.append(llm_answer)
                        output.append("")
                        output.append("-"*80)
                        output.append("📚 Крыніцы (факты з базы):")
                        output.append("")

                output.append(f"✅ Знойдзена фактаў: {len(results)}")
                output.append("")

                for i, r in enumerate(results, 1):
                    # Поўны тэкст без абразання
                    output.append(f"{i}. 📖 {r}")
                    output.append("")

                output.append("-"*80)
                output.append("💡 Карысная інфармацыя:")
                output.append(f"   • Усяго фактаў у базе: {len(self.facts)}")
                output.append(f"   • Індэксаваных слоў: {len(self.entity_index)}")
                output.append(f"   • Задавальненне сістэмы: {self.pleasure:.1f}")
                output.append(f"   • LLM: {'✅ ' + self.llm.provider if self.llm.enabled else '❌ Адключаны'}")

            output.append("")
            output.append("="*80)

            return "\n".join(output)

        except Exception as e:
            logger.error(f"Памылка фарматавання: {e}")
            return "❌ Памылка пры фарматаванні адказу"

    def answer_with_llm(self, question):
        """
        Адказ з поўнай LLM генерацыяй (RAG)
        
        Args:
            question: Пытанне карыстальніка
        
        Returns:
            Тэкставы адказ ад LLM
        """
        if not self.llm.enabled:
            return "⚠️ LLM адключаны. Выкарыстоўвайце ./run.sh llm-on для ўключэння."
        
        # Пошук фактаў
        facts = self.answer(question, use_llm_ranking=False)
        
        if not facts:
            return "❌ Нічога не знойдзена ў базе."
        
        # Генерацыя адказу
        return self.llm.generate(question, facts)

    def get_stats(self):
        return {
            'facts': len(self.facts),
            'associations': len(self.associations),
            'indexed_words': len(self.entity_index),
            'pleasure': self.pleasure,
            'goals': len(self.goals)
        }

    # Метады для кіравання кнігамі

    def get_book_manager(self) -> BookManager:
        """Атрыманне менеджара кніг"""
        return BookManager()

    def add_book(self, book_text: str, book_name: str, parse_mode: str = 'sentences') -> int:
        """
        Дадаванне кнігі ў базу
        
        Args:
            book_text: Тэкст кнігі
            book_name: Назва кнігі
            parse_mode: 'sentences' ці 'chapters'
        
        Returns:
            Колькасць дададзеных фактаў
        """
        book_mgr = self.get_book_manager()
        new_facts = book_mgr.add_book_to_facts(book_text, book_name, parse_mode)
        
        # Захаванне новых фактаў
        book_mgr.save_facts(new_facts)
        
        # Даданне ў бягучую базу
        self.facts.extend(new_facts)
        
        # Пераіндэксацыя
        self.build_full_index()
        self.calculate_idf()
        
        logger.info(f"📚 Дададзена кніга '{book_name}': {len(new_facts)} фактаў")
        return len(new_facts)

    def get_books_list(self) -> List[Dict]:
        """Атрыманне спісу кніг"""
        book_mgr = self.get_book_manager()
        return book_mgr.get_book_list()

    def get_books_stats(self) -> Dict:
        """Статыстыка па кнігах"""
        book_mgr = self.get_book_manager()
        return book_mgr.get_statistics()

    def search_in_books(self, query: str, book_name: str = None) -> List[Dict]:
        """Пошук па кнігах"""
        book_mgr = self.get_book_manager()
        return book_mgr.search_in_books(query, book_name)

    def reindex_all(self):
        """Поўная пераіндэксацыя ўсіх фактаў"""
        logger.info("🔄 Поўная пераіндэксацыя...")
        self.build_full_index()
        self.calculate_idf()
        logger.info(f"✅ Індэкс гатовы: {len(self.entity_index)} слоў")


def main():
    print("\n" + "="*80)
    print("🧠 БЕЛЭТАЛОН v0.1")
    print("="*80)
    print()
    print("📚 Інтэлектуальная пошукавая сістэма па гісторыі Беларусі")
    print()

    engine = BelarusUltimateEngine()

    stats = engine.get_stats()
    print(f"📊 Статыстыка сістэмы:")
    print(f"   • Фактаў у базе: {stats['facts']:,}")
    print(f"   • Індэксаваных слоў: {stats['indexed_words']:,}")
    print(f"   • Асацыяцый: {stats['associations']}")
    print()

    print("💡 Даступныя каманды:")
    print("   • 'выйсці' — завяршэнне працы")
    print("   • 'статыстыка' — поўная інфармацыя пра сістэму")
    print("   • 'тэст' — хуткі тэст пошуку")
    print()
    print("📝 Прыклады пытанняў:")
    print("   • Хто такі Кастусь Каліноўскі?")
    print("   • Што такое Статут 1588 года?")
    print("   • Вайна 1812 года ў Беларусі")
    print("   • Грунвальдская бітва 1410 года")
    print("   • Што такое БНР?")
    print()
    print("="*80)
    print()

    while True:
        try:
            q = input("❓ Пытанне: ").strip()

            if q.lower() in ['выйсці', 'exit', 'quit']:
                print("\n" + "="*80)
                print("👋 Да пабачэння! Дзякуй за выкарыстанне БелЭталон-2!")
                print("="*80 + "\n")
                break

            if q.lower() == 'статыстыка':
                stats = engine.get_stats()
                print("\n" + "="*80)
                print("📊 ПОЎНАЯ СТАТЫСТЫКА СІСТЭМЫ")
                print("="*80)
                print(f"   Фактаў у базе:        {stats['facts']:,}")
                print(f"   Індэксаваных слоў:    {stats['indexed_words']:,}")
                print(f"   Асацыяцый:            {stats['associations']}")
                print(f"   Мэтаў:                {stats['goals']}")
                print(f"   Задавальненне:        {engine.pleasure:.1f}")
                print("="*80 + "\n")
                continue

            if q.lower() == 'тэст':
                print("\n" + "="*80)
                print("🧪 ХУТКІ ТЭСТ ПОШУКУ")
                print("="*80)
                test_questions = [
                    "Хто такі Кастусь Каліноўскі?",
                    "Што такое Статут 1588?",
                    "Вайна 1812 года",
                    "Што такое БНР?",
                ]
                for tq in test_questions:
                    print(f"\n❓ {tq}")
                    print("-"*60)
                    print(engine.answer_formatted(tq))
                continue

            if not q:
                continue

            print("\n" + "="*80)
            print(engine.answer_formatted(q))
            print("="*80 + "\n")

        except (EOFError, KeyboardInterrupt):
            print("\n\n" + "="*80)
            print("👋 Да пабачэння! Дзякуй за выкарыстанне БелЭталон-2!")
            print("="*80 + "\n")
            break


if __name__ == "__main__":
    main()
