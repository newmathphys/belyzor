#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📖 ЗАГРУЗКА СЛОЎНІКАЎ І АЎТА-ВЫВУЧЭННЕ ПРАВІЛАЎ

Аўтаматычная загрузка слоўнікавых дадзеных і вывучэнне марфалагічных узораў
"""

import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple


class DictionaryLoader:
    """Загрузка слоўнікаў з розных фарматаў"""

    def __init__(self, dict_path: str = "data/raw/dictionaries"):
        self.dict_path = Path(dict_path)
        self.words = defaultdict(list)  # слова → [формы]
        self.lemmas = {}  # форма → лема

    def load_all_dictionaries(self):
        """Загрузіць усе даступныя слоўнікі"""
        print("📚 Загрузка слоўнікаў...")

        # Загрузка DSL слоўнікаў
        self._load_dsl_dictionaries()

        # Загрузка тэкставых слоўнікаў
        self._load_text_dictionaries()

        # Загрузка HTML слоўнікаў (спрошчана)
        self._load_html_dictionaries()

        print(f"✅ Загружана слоўнікаў: {len(self.words)}")

    def _load_dsl_dictionaries(self):
        """Загрузка слоўнікаў у фармаце DSL"""
        dsl_files = list(self.dict_path.glob("**/*.dsl"))

        for dsl_file in dsl_files:
            if dsl_file.name.endswith('_abrv.dsl'):
                continue  # Прапускам скарачэнні

            print(f"   📖 {dsl_file.name}...")
            self._parse_dsl(dsl_file)

    def _parse_dsl(self, dsl_file: Path):
        """Парсінг DSL файла"""
        with open(dsl_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # DSL фармат:
        # "Лема"
        #   [t] форма1, форма2, форма3
        #   [m] прыклад выкарыстання

        pattern = r'"([^"]+)"\s*\n([\s\S]*?)(?=\n\s*"|\Z)'
        matches = re.findall(pattern, content)

        for lemma, forms_block in matches:
            # Выманне форм
            forms_match = re.search(r'\[t\]\s*(.+?)(?:\n|\[)', forms_block)
            if forms_match:
                forms_text = forms_match.group(1)
                forms = [f.strip() for f in re.split(r'[;,]', forms_text)]

                self.words[lemma.lower()].extend(forms)
                for form in forms:
                    self.lemmas[form.lower()] = lemma.lower()

    def _load_text_dictionaries(self):
        """Загрузка тэкставых слоўнікаў (_abbr.txt)"""
        txt_files = list(self.dict_path.glob("**/*_abbr.txt"))

        for txt_file in txt_files:
            print(f"   📄 {txt_file.name}...")
            self._parse_text_dict(txt_file)

    def _parse_text_dict(self, txt_file: Path):
        """Парсінг тэкставага слоўніка"""
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Фармат: скарачэнне = поўная форма
                if '=' in line:
                    abbr, full = line.split('=', 1)
                    self.words[abbr.strip().lower()].append(full.strip().lower())
                    self.lemmas[full.strip().lower()] = abbr.strip().lower()

    def _load_html_dictionaries(self):
        """Загрузка HTML слоўнікаў (спрошчана)"""
        html_files = [
            self.dict_path / "klyshka" / "klyshka.html",
            self.dict_path / "tsblm" / "tsblm.html",
            self.dict_path / "tsblm2022" / "tsblm2022.html",
        ]

        for html_file in html_files:
            if html_file.exists():
                print(f"   🌐 {html_file.name}...")
                self._parse_html_dict(html_file)

    def _parse_html_dict(self, html_file: Path):
        """Спрошчаны парсінг HTML слоўніка"""
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Выманне слоў з HTML (спрошчана)
        # Шукаем тэгі з словамі
        word_pattern = r'<[a-z]+[^>]*>([^<]+)</[a-z]+>'
        words = re.findall(word_pattern, content)

        for word in words[:10000]:  # Абмяжоўваем для хуткасці
            word_clean = re.sub(r'<[^>]+>', '', word).strip().lower()
            if word_clean and len(word_clean) >= 3:
                self.words[word_clean].append(word_clean)


class FormLearner:
    """Аўта-вывучэнне марфалагічных форм з фактаў"""

    def __init__(self):
        self.word_forms = defaultdict(list)  # лема → [формы]
        self.patterns = []  # вывучаныя ўзоры
        self.fact_path = Path("data/etalons/facts.json")

    def learn_from_facts(self, max_facts: int = 30000):
        """Вывучэнне форм з фактаў"""
        print("\n🧠 Вывучэнне форм з фактаў...")

        if not self.fact_path.exists():
            print("   ❌ Файл facts.json не знойдзены")
            return

        with open(self.fact_path, 'r', encoding='utf-8') as f:
            facts = json.load(f)

        # Збор усіх слоў і іх кантэкстаў
        word_contexts = defaultdict(list)

        for i, fact in enumerate(facts[:max_facts]):
            if i % 5000 == 0:
                print(f"   Апрацавана {i}/{max_facts}")

            text = fact['fact'].lower()
            words = re.findall(r'[а-яёўі\'’]+', text)

            for j, word in enumerate(words):
                if len(word) >= 3:
                    # Кантэкст - суседнія словы
                    context_start = max(0, j-2)
                    context_end = min(len(words), j+3)
                    context = words[context_start:context_end]
                    word_contexts[word].append(context)

        # Аналіз форм слоў
        print("   Аналіз марфалагічных узораў...")
        self._analyze_word_forms(word_contexts)

        # Вывучэнне правілаў
        print("   Вывучэнне правілаў скланення...")
        self._learn_declension_patterns()

        print(f"✅ Вывучана форм: {len(self.word_forms)}")
        print(f"✅ Вывучана правілаў: {len(self.patterns)}")

    def _analyze_word_forms(self, word_contexts: Dict[str, List]):
        """Аналіз форм аднаго кораня"""
        # Групоўка слоў па коранях
        roots = defaultdict(list)

        for word in word_contexts.keys():
            # Вылучэнне кораня (спрошчана - апошнія 3-5 літар)
            if len(word) > 5:
                root = word[:-2]  # Адсякаем канчатак
                roots[root].append(word)

        # Пошук формаў з аднолькавым коранем
        for root, forms in roots.items():
            if len(forms) >= 2:
                # Гэта магчымыя формы аднаго слова
                self.word_forms[root].extend(forms)

    def _learn_declension_patterns(self):
        """Вывучэнне ўзораў скланення"""
        # Тыповыя канчаткі для беларускай мовы
        declension_patterns = [
            # Мужчынскі род
            (r'(.+)ага$', r'\1'),    # прыметнікі
            (r'(.+)аму$', r'\1'),
            (r'(.+)ім$', r'\1'),
            (r'(.+)а$', r'\1'),      # назоўнікі
            (r'(.+)у$', r'\1'),
            (r'(.+)ом$', r'\1'),

            # Жаночы род
            (r'(.+)ы$', r'\1а'),
            (r'(.+)і$', r'\1я'),
            (r'(.+)у$', r'\1у'),
            (r'(.+)ой$', r'\1а'),
            (r'(.+)ай$', r'\1а'),

            # Сярэдні род
            (r'(.+)а$', r'\1о'),
            (r'(.+)о$', r'\1о'),
            (r'(.+)у$', r'\1о'),
            (r'(.+)ам$', r'\1о'),

            # Множны лік
            (r'(.+)ы$', r'\1'),
            (r'(.+)і$', r'\1'),
            (r'(.+)аў$', r'\1'),
            (r'(.+)ам$', r'\1'),
            (r'(.+)ах$', r'\1'),
        ]

        self.patterns = declension_patterns

    def get_learned_rules(self) -> Dict[str, str]:
        """Вярнуць вывучаныя правілы як слоўнік выключэнняў"""
        exceptions = {}

        for root, forms in self.word_forms.items():
            if len(forms) >= 3:
                # Знойдзена некалькі форм - вызначаем асноўную
                # Асноўная - найбольш кароткая ці тая, што заканчваецца на зычны
                base_form = min(forms, key=len)

                for form in forms:
                    if form != base_form:
                        exceptions[form] = base_form

        return exceptions

    def export_rules(self, output_path: str = "src/core/learned_rules.json"):
        """Экспарт вывучаных правілаў"""
        rules = self.get_learned_rules()

        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)

        print(f"   📁 Правілы захаваны: {output_file}")
        print(f"   📊 Колькасць правілаў: {len(rules)}")


def main():
    """Галоўная функцыя"""
    print("="*80)
    print("📖 ЗАГРУЗКА СЛОЎНІКАЎ І АЎТА-ВЫВУЧЭННЕ ПРАВІЛАЎ")
    print("="*80)

    # Загрузка слоўнікаў
    loader = DictionaryLoader()
    loader.load_all_dictionaries()

    # Вывучэнне з фактаў
    learner = FormLearner()
    learner.learn_from_facts()

    # Экспарт правілаў
    learner.export_rules()

    # Статыстыка
    print("\n" + "="*80)
    print("📊 ВЫНІКІ")
    print("="*80)
    print(f"   Загружана слоўнікавых слоў: {len(loader.words)}")
    print(f"   Знойдзена форм у слоўніках: {len(loader.lemmas)}")
    print(f"   Вывучана форм з фактаў: {len(learner.word_forms)}")
    print(f"   Вывучана правілаў: {len(learner.patterns)}")
    print("="*80)


if __name__ == "__main__":
    main()
