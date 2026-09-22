"""
БелУзор v2026: NLP апрацоўка беларускага тэксту

Інтэграцыя:
- Stanza (Stanford NLP) для дакладнай лематызацыі
- SpaCy з падтрымкай беларускай мовы
- NER (Named Entity Recognition) для выдзялення:
  * Гістарычных асоб
  * Дат
  * Геаграфічных назваў
  * Падзей
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Імпарт з агароджваннем для апцыянальных залежнасцей
try:
    import stanza
    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False
    print("⚠️ Stanza не ўсталяваны. Лематызацыя будзе абмежавана.")

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️ SpaCy не ўсталяваны.")


class EntityType(Enum):
    """Тыпы іменаваных сутнасцей."""
    PERSON = "PERSON"  # Гістарычныя асобы
    LOCATION = "LOC"  # Геаграфічныя назвы
    DATE = "DATE"  # Даты
    EVENT = "EVENT"  # Гістарычныя падзеі
    ORGANIZATION = "ORG"  # Арганізацыі
    WORK_OF_ART = "WORK_OF_ART"  # Кнігі, дакументы
    LAW = "LAW"  # Законы, статуты


@dataclass
class NamedEntity:
    """Іменаваная сутнасць."""
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TokenInfo:
    """Інфармацыя пра токен."""
    text: str
    lemma: str
    pos: str  # Часціна мовы
    tag: str  # Дэталёвы тэг
    dep: str  # Сінтаксічная залежнасць
    is_stop: bool = False


class BelarusianNLPProcessor:
    """Апрацоўшчык беларускага тэксту з NLP функцыямі."""
    
    def __init__(
        self,
        use_stanza: bool = True,
        use_spacy: bool = False,
        download_models: bool = True
    ):
        """
        Ініцыялізацыя NLP працэсара.
        
        Args:
            use_stanza: Выкарыстоўваць Stanza для лематызацыі
            use_spacy: Выкарыстоўваць SpaCy для NER
            download_models: Ці спампоўваць мадэлі пры першым запуску
        """
        self.use_stanza = use_stanza and STANZA_AVAILABLE
        self.use_spacy = use_spacy and SPACY_AVAILABLE
        
        self.stanza_nlp = None
        self.spacy_nlp = None
        
        # Ініцыялізацыя Stanza
        if self.use_stanza:
            try:
                print("📥 Ініцыялізацыя Stanza для беларускай мовы...")
                if download_models:
                    stanza.download('be', verbose=False)
                self.stanza_nlp = stanza.Pipeline(
                    lang='be',
                    processors='tokenize,pos,lemma,depparse',
                    verbose=False
                )
                print("✅ Stanza гатова")
            except Exception as e:
                print(f"⚠️ Памылка ініцыялізацыі Stanza: {e}")
                self.use_stanza = False
        
        # Ініцыялізацыя SpaCy (калі ёсць беларуская мадэль)
        if self.use_spacy:
            try:
                print("📥 Ініцыялізацыя SpaCy...")
                # Спрабуем загрузіць беларускую мадэль
                try:
                    self.spacy_nlp = spacy.load("be_core_news_lg")
                except OSError:
                    # Калі няма - спрабуем рускую як fallback
                    print("⚠️ Беларуская мадэль не знойдзена. Спрабуем рускую...")
                    try:
                        self.spacy_nlp = spacy.load("ru_core_news_lg")
                    except OSError:
                        print("⚠️ Ніводная мадэль не знойдзена. NER будзе абмежаваны.")
                        self.use_spacy = False
                
                if self.spacy_nlp:
                    print("✅ SpaCy гатова")
            except Exception as e:
                print(f"⚠️ Памылка ініцыялізацыі SpaCy: {e}")
                self.use_spacy = False
        
        # Ручныя правілы для NER (fallback)
        self.ner_patterns = self._init_manual_ner_patterns()
    
    def _init_manual_ner_patterns(self) -> Dict[str, re.Pattern]:
        """Ініцыялізацыя ручных рэгулярных выразаў для NER."""
        patterns = {
            # Даты (гады, стагоддзі)
            'DATE': re.compile(r'\b(\d{1,4}(?:\s*-\s*\d{1,4})?|\d+[вх]\s*ст\.?)\b'),
            
            # Геаграфічныя назвы (спрашчона)
            'LOCATION': re.compile(r'\b(?:у|ў|з|да|ад)?\s*(Полацк|Менск|Вільня|Гродна|Берасьце|Віцебск|Магілёў|Тураў|Наваградак|Нясьвіж|Мір)\b'),
            
            # Гістарычныя асобы (вядомыя імёны)
            'PERSON': re.compile(r'\b(Францыск\s+Скарына|Леў\s+Сапега|Кастусь\s+Каліноўскі|Усяслаў\s+Чарадзей|Міндоўг|Вітаўт|Ягайла|Стэфан\s+Баторый)\b'),
            
            # Законы і дакументы
            'LAW': re.compile(r'\b(Статут\s+ВКЛ|Прывілей|Грамата|Канстытуцыя\s+3\s+мая)\b'),
            
            # Арганізацыі
            'ORGANIZATION': re.compile(r'\b(Вялікае\s+Княства\s+Літоўскае|Рэч\s+Паспалітая|Расійская\s+імперыя|СССР)\b'),
        }
        return patterns
    
    def tokenize_and_lemmatize(self, text: str) -> List[TokenInfo]:
        """
        Такенізацыя і лематызацыя тэксту.
        
        Args:
            text: Уваходны тэкст
            
        Returns:
            Спіс токенаў з лемамі
        """
        tokens = []
        
        if self.use_stanza and self.stanza_nlp:
            # Выкарыстанне Stanza
            doc = self.stanza_nlp(text)
            
            for sentence in doc.sentences:
                for word in sentence.words:
                    token = TokenInfo(
                        text=word.text,
                        lemma=word.lemma or word.text,
                        pos=word.upos or "X",
                        tag=word.xpos or "_",
                        dep=word.deprel or "_",
                        is_stop=self._is_stop_word(word.text)
                    )
                    tokens.append(token)
        
        elif self.use_spacy and self.spacy_nlp:
            # Выкарыстанне SpaCy
            doc = self.spacy_nlp(text)
            
            for token in doc:
                token_info = TokenInfo(
                    text=token.text,
                    lemma=token.lemma_ or token.text,
                    pos=token.pos_ or "X",
                    tag=token.tag_ or "_",
                    dep=token.dep_ or "_",
                    is_stop=token.is_stop
                )
                tokens.append(token_info)
        
        else:
            # Fallback: простае разбіццё на словы
            words = re.findall(r'\w+|\W+', text)
            for word in words:
                if word.strip():
                    token = TokenInfo(
                        text=word,
                        lemma=word.lower(),
                        pos="X",
                        tag="_",
                        dep="_",
                        is_stop=self._is_stop_word(word)
                    )
                    tokens.append(token)
        
        return tokens
    
    def extract_entities(self, text: str) -> List[NamedEntity]:
        """
        Выдзяленне іменаваных сутнасцей (NER).
        
        Args:
            text: Уваходны тэкст
            
        Returns:
            Спіс знойдзеных сутнасцей
        """
        entities = []
        
        # 1. Выкарыстанне SpaCy для NER (калі даступны)
        if self.use_spacy and self.spacy_nlp:
            doc = self.spacy_nlp(text)
            
            for ent in doc.ents:
                entity_type = self._map_spacy_entity_type(ent.label_)
                
                if entity_type:
                    entity = NamedEntity(
                        text=ent.text,
                        entity_type=entity_type,
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        confidence=0.9,
                        metadata={"source": "spacy", "label": ent.label_}
                    )
                    entities.append(entity)
        
        # 2. Ручное NER з дапамогай рэгулярных выразаў
        manual_entities = self._extract_manual_entities(text)
        
        # Аб'яднанне і выдаленне дублікатаў
        existing_spans = {(e.start_pos, e.end_pos) for e in entities}
        
        for manual_ent in manual_entities:
            if (manual_ent.start_pos, manual_ent.end_pos) not in existing_spans:
                entities.append(manual_ent)
                existing_spans.add((manual_ent.start_pos, manual_ent.end_pos))
        
        # Сартаванне па пазіцыі
        entities.sort(key=lambda x: x.start_pos)
        
        return entities
    
    def _extract_manual_entities(self, text: str) -> List[NamedEntity]:
        """Выдзяленне сутнасцей з дапамогай рэгулярных выразаў."""
        entities = []
        
        for entity_type, pattern in self.ner_patterns.items():
            for match in pattern.finditer(text):
                try:
                    etype = EntityType(entity_type)
                    entity = NamedEntity(
                        text=match.group(),
                        entity_type=etype,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=0.7,  # Ніжэйшая ўпэўненасць для regex
                        metadata={"source": "regex"}
                    )
                    entities.append(entity)
                except ValueError:
                    continue
        
        return entities
    
    def _map_spacy_entity_type(self, label: str) -> Optional[EntityType]:
        """Маппінг этыкетак SpaCy да нашых тыпаў."""
        mapping = {
            'PER': EntityType.PERSON,
            'PERSON': EntityType.PERSON,
            'LOC': EntityType.LOCATION,
            'LOCATION': EntityType.LOCATION,
            'GPE': EntityType.LOCATION,
            'DATE': EntityType.DATE,
            'TIME': EntityType.DATE,
            'EVENT': EntityType.EVENT,
            'ORG': EntityType.ORGANIZATION,
            'ORGANIZATION': EntityType.ORGANIZATION,
            'WORK_OF_ART': EntityType.WORK_OF_ART,
            'LAW': EntityType.LAW,
        }
        return mapping.get(label)
    
    def _is_stop_word(self, word: str) -> bool:
        """Праверка стоп-слоў."""
        stop_words = {
            'і', 'ў', 'у', 'на', 'з', 'са', 'да', 'ад', 'каб', 'як',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'это', 'что', 'как', 'так', 'же', 'ли', 'бы', 'не', 'ни'
        }
        return word.lower() in stop_words
    
    def get_summary_stats(self, text: str) -> Dict[str, Any]:
        """
        Атрыманне статыстыкі тэксту.
        
        Args:
            text: Уваходны тэкст
            
        Returns:
            Слоўнік са статыстыкай
        """
        tokens = self.tokenize_and_lemmatize(text)
        entities = self.extract_entities(text)
        
        # Падлік частотнасці слоў
        word_freq = {}
        for token in tokens:
            if not token.is_stop and token.pos not in ['PUNCT', 'SPACE']:
                lemma = token.lemma.lower()
                word_freq[lemma] = word_freq.get(lemma, 0) + 1
        
        # Тыпы сутнасцей
        entity_types = {}
        for entity in entities:
            etype = entity.entity_type.value
            entity_types[etype] = entity_types.get(etype, 0) + 1
        
        return {
            "total_tokens": len(tokens),
            "unique_lemmas": len(set(t.lemma for t in tokens)),
            "total_entities": len(entities),
            "entity_types": entity_types,
            "top_words": sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10],
            "sentences_count": text.count('.') + text.count('!') + text.count('?')
        }
    
    def detect_orthography_advanced(self, text: str) -> Tuple[str, float]:
        """
        Пашыранае вызначэнне правапісу (наркамаўка/тарашкевіца).
        
        Args:
            text: Уваходны тэкст
            
        Returns:
            (тып правапісу, упэўненасць)
        """
        tarask_markers = [
            (r'\bў\b', 2),  # ў
            (r'\bьшч\b', 3),  # мяккі знак перад щ
            (r'\бэ\b', 2),  # э
            (r'(-|\s)ж(\s|$)', 2),  # ж пасля зычных
            (r'\бый\b', 1),  # -ый канчаткі
            (r'\бчаго\b', 3),  # чаго замест чего
            (r'\бсь\b', 2),  # сьмякчэнне
        ]
        
        narkamauka_markers = [
            (r'\бв\b(?=[аоуэы])', 1),  # в перад галоснымі
            (r'\бзгодна\b', 1),  # згодна
            (r'\бпа\b', 1),  # па
        ]
        
        tarask_score = 0
        narkamauka_score = 0
        
        for pattern, weight in tarask_markers:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            tarask_score += matches * weight
        
        for pattern, weight in narkamauka_markers:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            narkamauka_score += matches * weight
        
        total_score = tarask_score + narkamauka_score
        
        if total_score == 0:
            return "unknown", 0.5
        
        if tarask_score > narkamauka_score:
            confidence = tarask_score / total_score
            return "tarask", confidence
        else:
            confidence = narkamauka_score / total_score
            return "narkamauka", confidence


def main():
    """Прыклад выкарыстання NLP працэсара."""
    # Ініцыялізацыя
    processor = BelarusianNLPProcessor(
        use_stanza=True,
        use_spacy=False,
        download_models=False  # Не спампоўваць пры тэсце
    )
    
    # Тэставы тэкст
    text = """
    Францыск Скарына нарадзіўся ў Полацку каля 1490 года. 
    Ён заснаваў друкарства ва Усходняй Еўропе, выдаўшы Біблію ў 1517 годзе.
    Статут ВКЛ 1588 года быў створаны Львом Сапегам.
    """
    
    print(f"\n📝 Тэкст:\n{text}\n")
    
    # Лематызацыя
    print("🔤 Лематызацыя:")
    tokens = processor.tokenize_and_lemmatize(text[:100])  # Абмежаванне для прыкладу
    for token in tokens[:15]:
        print(f"  {token.text:15} → {token.lemma:15} ({token.pos})")
    
    # NER
    print("\n🏷️ Іменаваныя сутнасці:")
    entities = processor.extract_entities(text)
    for entity in entities:
        print(f"  {entity.text:30} | {entity.entity_type.value:15} | [{entity.start_pos}:{entity.end_pos}]")
    
    # Статыстыка
    print("\n📊 Статыстыка:")
    stats = processor.get_summary_stats(text)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Вызначэнне правапісу
    print("\n🔤 Вызначэнне правапісу:")
    ortho, conf = processor.detect_orthography_advanced(text)
    print(f"  Тып: {ortho}, Упэўненасць: {conf:.2f}")


if __name__ == "__main__":
    main()
