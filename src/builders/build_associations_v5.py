#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔗 БУДАЎНІК АСАЦЫЯЦЫЙ v5 — ПОЎНАЕ АБНАЎЛЕННЕ
"""

import json
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.logger import logger

class AssociationBuilderV5:
    def __init__(self):
        self.facts = []
        self.associations = defaultdict(lambda: defaultdict(float))
        self.entity_freq = defaultdict(int)
        self.entity_cooccur = defaultdict(lambda: defaultdict(int))
        
        # Поўны спіс паняццяў (50 → 100+)
        self.real_entities = [
            # Асобы (было)
            'кастусь', 'каліноўскі', 'францыск', 'скарына', 'сапега',
            'астрожскі', 'тызенгаўз', 'касцюшка', 'вітаўт', 'ягайла',
            'баторый', 'радзівіл', 'агінскі', 'дамейка', 'нарбут',
            
            # 🔥 НОВЫЯ АСОБЫ
            'міндоўг', 'міндаўг', 'гедымін', 'ягайла', 'альгерд',
            'жыгімонт', 'жыгімонт стары', 'жыгімонт аўгуст',
            'баторы', 'свідрыгайла', 'вятоўт', 'кейстут',
            'луцкевіч', 'ластоўскі', 'чарот', 'купала', 'колас',
            'багдановіч', 'чарвякоў', 'караткевіч', 'быкаў',
            
            # Гарады (было)
            'полацк', 'мінск', 'бабруйск', 'віцебск', 'магілёў',
            'гродна', 'брэст', 'гомель', 'пінск', 'ліда', 'навагрудак',
            
            # 🔥 НОВЫЯ ГАРАДЫ
            'слонім', 'кобрын', 'орша', 'мазыр', 'рэчыца',
            'клецк', 'несвіж', 'мір', 'заслаўе', 'тураў',
            
            # Дзяржавы і тэрміны (было)
            'вкл', 'бнр', 'бсср', 'ссср', 'рэч паспалітая', 'вялікае княства',
            
            # 🔥 НОВЫЯ ТЭРМІНЫ
            'вялікая айчынная вайна', 'вайна 1941', 'вайна 1944',
            'другая сусветная вайна', 'першая сусветная вайна',
            'айчынная вайна 1812', 'вайна 1812',
            'паўстанне 1830', 'паўстанне 1831', 'паўстанне 1863', 'паўстанне 1864',
            'падзелы рэчы паспалітай', 'першы падзел', 'другі падзел', 'трэці падзел',
            'брэсцкая унія', 'люблінская унія', 'крэўская унія', 'гарадзельская унія',
            
            # Права і палітыка (было)
            'статут', 'прывілей', 'канстытуцыя', 'унія', 'сойм', 'рада',
            'падзел', 'паўстанне', 'рэвалюцыя', 'вайна', 'бітва',
            
            # 🔥 НОВЫЯ ПРАВАВЫЯ ТЭРМІНЫ
            'статут 1529', 'статут 1566', 'статут 1588',
            'літоўскі статут', 'статут вялікага княства',
            'канстытуцыя 3 мая', 'канстытуцыя рэчы паспалітай',
            
            # Даты (было)
            '1863', '1864', '1812', '1941', '1944', '1917', '1921', '1991',
            '1588', '1569', '1385', '1410',
            
            # 🔥 НОВЫЯ ДАТЫ
            '1772', '1793', '1795', '1918', '1919', '1920', '1939',
            '1506', '1514', '1529', '1563', '1579', '1654', '1700',
            
            # Этнаграфія (было)
            'крывічы', 'радзімічы', 'дрыгавічы', 'яцьвягі',
            
            # 🔥 НОВЫЯ ПАНЯЦЦІ
            'хатынь', 'хатыньская трагедыя', 'катастрофа',
            'дэкларацыя аб суверэнітэце', 'суверэнітэт',
            'незалежнасць', 'беларуская незалежнасць',
            'беларуская народная рэспубліка', 'бнр',
            'беларуская савецкая сацыялістычная рэспубліка', 'бсср',
            'саюз савецкіх сацыялістычных рэспублік', 'ссср',
        ]
        
        # Лемматызацыя (словоформа → асноўная форма)
        self.lemmatized_forms = {
            'паспалітай': 'рэч паспалітая',
            'падзелы': 'падзел',
            'падзяліць': 'падзел',
            'паспалітых': 'рэч паспалітая',
            'княстваў': 'княства',
            'каранацыі': 'каранацыя',
            'ўніі': 'унія',
            'хатыні': 'хатынь',
            'вайны': 'вайна',
            'войны': 'вайна',
            'бітвы': 'бітва',
            'статуты': 'статут',
            'статутаў': 'статут',
        }
        
        # Складаныя тэрміны (шукаць спачатку)
        self.complex_terms = [
            'вялікая айчынная вайна',
            'другая сусветная вайна',
            'першая сусветная вайна',
            'вялікае княства літоўскае',
            'рэч паспалітая',
            'дэкларацыя аб дзяржаўным суверэнітэце',
            'беларуская народная рэспубліка',
            'беларуская савецкая сацыялістычная рэспубліка',
            'падзелы рэчы паспалітай',
            'статут вялікага княства літоўскага',
        ]
        
        self.load_facts()
        logger.info(f"Будаўнік ініцыялізаваны, паняццяў: {len(self.real_entities)}")
    
    def load_facts(self):
        facts_file = Path(__file__).parent.parent.parent / "data/etalons/facts.json"
        if facts_file.exists():
            with open(facts_file, 'r', encoding='utf-8') as f:
                self.facts = json.load(f)
            logger.info(f"📚 Загружана фактаў: {len(self.facts)}")
    
    def extract_entities(self, text):
        """Палепшанае выманне паняццяў"""
        found = set()
        text_lower = text.lower()
        
        # 1. Шукаем складаныя тэрміны (спачатку!)
        for term in self.complex_terms:
            if term in text_lower:
                found.add(term)
        
        # 2. Шукаем звычайныя паняцці
        for entity in self.real_entities:
            # Дакладнае супадзенне
            if re.search(r'\b' + re.escape(entity) + r'\b', text_lower):
                found.add(entity)
                continue
            
            # Супадзенне з марфалогіяй
            pattern = r'\b' + re.escape(entity) + r'(?:[іыяюяў]?(?:ага|аму|ым|ымі|ай|ую|ія)?)?\b'
            if re.search(pattern, text_lower):
                found.add(entity)
                continue
            
            # Для кароткіх слоў (імёны)
            if len(entity) <= 8:
                base = entity[:-2] if len(entity) > 4 else entity
                if re.search(r'\b' + re.escape(base) + r'[а-яёўі\'’]{0,4}\b', text_lower):
                    found.add(entity)
        
        # 3. Лемматызацыя для вядомых формаў
        words = re.findall(r'[а-яёўі\'’]+', text_lower)
        for word in words:
            if word in self.lemmatized_forms:
                found.add(self.lemmatized_forms[word])
        
        return list(found)
    
    def build_associations(self):
        logger.info("🔍 Аналіз сустрэчнасці паняццяў...")
        
        for i, fact in enumerate(self.facts):
            if i % 5000 == 0 and i > 0:
                logger.info(f"   Апрацавана {i}/{len(self.facts)}")
            
            entities = self.extract_entities(fact['fact'])
            
            for e in entities:
                self.entity_freq[e] += 1
            
            for i1, e1 in enumerate(entities):
                for e2 in entities[i1+1:]:
                    self.entity_cooccur[e1][e2] += 1
        
        logger.info("📊 Разлік сілы асацыяцый...")
        
        result = {}
        for e1 in self.real_entities:
            if self.entity_freq[e1] >= 3:
                assoc = {}
                for e2 in self.real_entities:
                    if e1 != e2 and self.entity_cooccur[e1][e2] >= 2:
                        strength = self.entity_cooccur[e1][e2] / self.entity_freq[e1]
                        if strength >= 0.1:
                            assoc[e2] = round(strength, 3)
                if assoc:
                    result[e1] = assoc
        
        output_path = Path(__file__).parent.parent.parent / "data/etalons/associations_v5.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Асацыяцыі захаваны: {len(result)} паняццяў")
        
        # Паказваем прыклады
        logger.info("\n🔍 Прыклады новых асацыяцый:")
        for e1 in list(result.keys())[:15]:
            top = sorted(result[e1].items(), key=lambda x: -x[1])[:3]
            if top:
                logger.info(f"   • {e1} → {', '.join([f'{e2} ({s})' for e2, s in top])}")
        
        return result

def main():
    print("="*80)
    print("�� БУДАЎНІК АСАЦЫЯЦЫЙ v5 — ПОЎНАЕ АБНАЎЛЕННЕ")
    print("="*80)
    
    builder = AssociationBuilderV5()
    builder.build_associations()

if __name__ == "__main__":
    main()
