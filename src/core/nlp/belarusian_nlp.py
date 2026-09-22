#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 БЕЛУЗОР v2026 — NLP апрацоўка беларускага тэксту (Stanza/SpaCy)

Падтрымка:
- Stanza (Stanford NLP) для беларускага мовы
- Вылучэнне сутнасцей (NER)
- Лематызацыя з улікам кантэксту
- Марфалагічны аналіз
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from src.core.logger import logger


@dataclass
class Token:
    """Токен з марфалагічнай інфармацыяй"""
    text: str
    lemma: str
    pos: str  # часціна мовы
    tag: str  # дэталёвы тэг
    dep: str  # сінтаксічная залежнасць
    head: int  # індэс галавы
    ner: str = ""  # NER тэг
    
    def __post_init__(self):
        if not self.ner:
            self.ner = "O"


@dataclass
class Entity:
    """Выдзеленая сутнасць (NER)"""
    text: str
    type: str  # PERSON, LOCATION, DATE, ORGANIZATION і г.д.
    start: int
    end: int
    confidence: float = 1.0


class BelarusianNLP:
    """
    NLP апрацоўка беларускага тэксту
    
    Выкарыстоўвае Stanza або SpaCy для:
    - Токенізацыі
    - Лематызацыі з улікам кантэксту
    - Вылучэння сутнасцей (NER)
    - Сінтаксічнага аналізу
    """
    
    def __init__(self, backend: str = "stanza", lang: str = "be"):
        """
        Ініцыялізацыя NLP
        
        Args:
            backend: "stanza" ці "spacy"
            lang: код мовы ("be" для беларускага)
        """
        self.backend = backend
        self.lang = lang
        self.pipeline = None
        self.nlp_model = None
        
        # Загрузка мадэлі
        self._load_model()
    
    def _load_model(self):
        """Загрузка NLP мадэлі"""
        try:
            if self.backend == "stanza":
                self._load_stanza()
            elif self.backend == "spacy":
                self._load_spacy()
            else:
                logger.warning(f"⚠️ Невядомы backend: {self.backend}")
                
        except ImportError as e:
            logger.warning(f"⚠️ NLP бібліятэкі не усталяваны: {e}")
            logger.info("💡 Выкарыстоўвайце заглушку або ўсталюйце: pip install stanza")
        except Exception as e:
            logger.error(f"❌ Памылка загрузкі NLP мадэлі: {e}")
    
    def _load_stanza(self):
        """Загрузка Stanza"""
        try:
            import stanza
            
            logger.info(f"📥 Загрузка Stanza для {self.lang}...")
            
            # Загрузка мадэлі
            stanza.download(self.lang, verbose=False)
            self.pipeline = stanza.Pipeline(
                lang=self.lang,
                processors='tokenize,pos,lemma,deparse,ner',
                verbose=False
            )
            
            logger.info("✅ Stanza загружана")
            
        except Exception as e:
            logger.warning(f"⚠️ Не ўдалося загрузіць Stanza: {e}")
            self.pipeline = None
    
    def _load_spacy(self):
        """Загрузка SpaCy"""
        try:
            import spacy
            
            logger.info(f"📥 Загрузка SpaCy для {self.lang}...")
            
            # Для беларускага можна выкарыстоўваць multilingual мадэль
            try:
                self.pipeline = spacy.load("be_core_news_sm")
            except OSError:
                # Калі беларуская мадэль не знойдзена
                logger.warning("⚠️ Беларуская мадэль SpaCy не знойдзена")
                logger.info("💡 Спрабуем Russian ці Ukrainian як fallback")
                try:
                    self.pipeline = spacy.load("ru_core_news_sm")
                except:
                    self.pipeline = None
            
            logger.info("✅ SpaCy загружана")
            
        except Exception as e:
            logger.warning(f"⚠️ Не ўдалося загрузіць SpaCy: {e}")
            self.pipeline = None
    
    def process(self, text: str) -> List[Token]:
        """
        Апрацоўка тэксту
        
        Args:
            text: тэкст для апрацоўкі
            
        Returns:
            Спіс Token з поўнай інфармацыяй
        """
        if not self.pipeline:
            # Заглушка без NLP
            return self._simple_tokenize(text)
        
        try:
            doc = self.pipeline(text)
            tokens = []
            
            for sentence in doc.sentences:
                for word in sentence.words:
                    token = Token(
                        text=word.text,
                        lemma=getattr(word, 'lemma', word.text.lower()),
                        pos=getattr(word, 'pos', 'X'),
                        tag=getattr(word, 'tags', ''),
                        dep=getattr(word, 'dep', 'root'),
                        head=getattr(word, 'head', 0),
                        ner=getattr(word, 'ner', 'O')
                    )
                    tokens.append(token)
            
            return tokens
            
        except Exception as e:
            logger.error(f"❌ Памылка апрацоўкі: {e}")
            return self._simple_tokenize(text)
    
    def _simple_tokenize(self, text: str) -> List[Token]:
        """Простая токенизация без NLP"""
        import re
        
        words = re.findall(r'[а-яёўі\']+|\d{4}|[^\w\s]', text, re.IGNORECASE)
        
        tokens = []
        for word in words:
            token = Token(
                text=word,
                lemma=word.lower(),
                pos='X',
                tag='',
                dep='root',
                head=0
            )
            tokens.append(token)
        
        return tokens
    
    def extract_entities(self, text: str) -> List[Entity]:
        """
        Вылучэнне іменаваных сутнасцей (NER)
        
        Args:
            text: тэкст для аналізу
            
        Returns:
            Спіс Entity
        """
        if not self.pipeline:
            # Простае правіла на аснове рэгулярак
            return self._simple_ner(text)
        
        try:
            doc = self.pipeline(text)
            entities = []
            
            # Stanza захоўвае NER у словах
            current_entity = None
            start_pos = 0
            
            for sentence in doc.sentences:
                char_offset = 0
                
                for word in sentence.words:
                    ner_tag = getattr(word, 'ner', 'O')
                    
                    if ner_tag != 'O':
                        if current_entity is None:
                            # Пачатак новай сутнасці
                            current_entity = {
                                'text': word.text,
                                'type': ner_tag,
                                'start': char_offset,
                                'end': char_offset + len(word.text)
                            }
                        elif ner_tag.startswith('I-') or ner_tag == current_entity['type']:
                            # Працяг сутнасці
                            current_entity['text'] += ' ' + word.text
                            current_entity['end'] = char_offset + len(word.text)
                        else:
                            # Канец папярэдняй і пачатак новай
                            if current_entity:
                                entities.append(Entity(**current_entity))
                            current_entity = {
                                'text': word.text,
                                'type': ner_tag,
                                'start': char_offset,
                                'end': char_offset + len(word.text)
                            }
                    
                    char_offset += len(word.text) + 1  # +1 для прабелу
                
                # Дадаць апошнюю сутнасць
                if current_entity:
                    entities.append(Entity(**current_entity))
                    current_entity = None
            
            return entities
            
        except Exception as e:
            logger.error(f"❌ Памылка NER: {e}")
            return self._simple_ner(text)
    
    def _simple_ner(self, text: str) -> List[Entity]:
        """Простае NER на аснове правілаў"""
        import re
        
        entities = []
        
        # Даты (гады)
        year_pattern = r'\b(\d{4})\b'
        for match in re.finditer(year_pattern, text):
            entities.append(Entity(
                text=match.group(1),
                type='DATE',
                start=match.start(),
                end=match.end()
            ))
        
        # Уласныя назвы (вялікія літары)
        proper_noun_pattern = r'\b([А-ЯЁЎІ][а-яёўі\']+(?:\s+[А-ЯЁЎІ][а-яёўі\']+)*)\b'
        for match in re.finditer(proper_noun_pattern, text):
            entity_text = match.group(1)
            # Фільтр кароткіх і частых слоў
            if len(entity_text) > 3 and entity_text not in ['Гэта', 'Такі', 'Сам']:
                entities.append(Entity(
                    text=entity_text,
                    type='PERSON',  # Меркавана асоба
                    start=match.start(),
                    end=match.end()
                ))
        
        return entities
    
    def lemmatize(self, text: str) -> str:
        """
        Лематызацыя тэксту
        
        Args:
            text: тэкст для лематызацыі
            
        Returns:
            Тэкст з лемамі
        """
        tokens = self.process(text)
        lemmas = [token.lemma for token in tokens]
        return ' '.join(lemmas)
    
    def get_lemmas(self, text: str) -> List[str]:
        """Атрыманне спісу лем"""
        tokens = self.process(text)
        return [token.lemma for token in tokens if token.pos not in ['PUNCT', 'SPACE']]
    
    def get_pos_tags(self, text: str) -> List[Tuple[str, str]]:
        """Атрыманне часцін мовы"""
        tokens = self.process(text)
        return [(token.text, token.pos) for token in tokens]
    
    def get_dependencies(self, text: str) -> List[Tuple[str, str, int]]:
        """Атрыманне сінтаксічных залежнасцей"""
        tokens = self.process(text)
        return [(token.text, token.dep, token.head) for token in tokens]
    
    def analyze_sentence(self, sentence: str) -> Dict:
        """
        Поўны аналіз сказа
        
        Returns:
            Dict з усёй інфармацыяй
        """
        tokens = self.process(sentence)
        entities = self.extract_entities(sentence)
        
        return {
            'text': sentence,
            'tokens': [
                {
                    'text': t.text,
                    'lemma': t.lemma,
                    'pos': t.pos,
                    'dep': t.dep
                }
                for t in tokens
            ],
            'entities': [
                {
                    'text': e.text,
                    'type': e.type,
                    'start': e.start,
                    'end': e.end
                }
                for e in entities
            ],
            'lemmatized': ' '.join(t.lemma for t in tokens),
            'length': len(tokens)
        }


def main():
    """Тэставанне NLP"""
    print("="*80)
    print("🧪 ТЭСТАВАННЕ NLP АПРАЦОЎКІ БЕЛАРУСКАГА ТЭКСТУ")
    print("="*80)
    
    # Ініцыялізацыя
    nlp = BelarusianNLP(backend="stanza")
    
    # Тэставы тэкст
    test_text = """
    Кастусь Каліноўскі нарадзіўся ў 1838 годзе ў вёсцы Мастаўляны.
    Ён быў адным з кіраўнікоў паўстання 1863 года супраць Расійскай імперыі.
    22 сакавіка 1864 года яго пакаралі смерцю ў Вільні на Лукішках.
    """
    
    print(f"\n📝 Тэкст: {test_text.strip()}")
    
    # Токенізацыя і лематызацыя
    print("\n✂️ Токенізацыя і лематызацыя:")
    tokens = nlp.process(test_text)
    
    for i, token in enumerate(tokens[:15], 1):  # Першыя 15 токенаў
        print(f"  {i:2}. {token.text:15} → {token.lemma:15} [{token.pos}]")
    
    # Вылучэнне сутнасцей
    print("\n🏷️ Вылучэнне сутнасцей (NER):")
    entities = nlp.extract_entities(test_text)
    
    for entity in entities:
        print(f"  • [{entity.type:12}] {entity.text:30} ({entity.start}-{entity.end})")
    
    # Поўны аналіз
    print("\n🔍 Поўны аналіз першага сказа:")
    sentence = "Кастусь Каліноўскі нарадзіўся ў 1838 годзе."
    analysis = nlp.analyze_sentence(sentence)
    
    print(f"  Лематызаваны: {analysis['lemmatized']}")
    print(f"  Колькасць токенаў: {analysis['length']}")
    print(f"  Сутнасці: {[e['text'] for e in analysis['entities']]}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
