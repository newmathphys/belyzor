#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧠 БЕЛУЗОР v2026 — Граф ведаў (Knowledge Graph) для гістарычных дадзеных

Падтрымка:
- Вылучэнне сутнасцей і сувязяў з тэксту
- Пабудова графа ведаў
- GraphRAG пошук
- Інтэграцыя з вектарным пошукам
"""

import json
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import defaultdict
from pathlib import Path

from src.core.logger import logger


@dataclass
class Entity:
    """Сутнасць у графе ведаў"""
    id: str
    name: str
    type: str  # PERSON, LOCATION, EVENT, DATE, ORGANIZATION
    metadata: Dict = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.id == other.id
        return False


@dataclass
class Relation:
    """Сувязь паміж сутнасцямі"""
    source: str  # ID крыніцы
    target: str  # ID мэты
    type: str    # тып сувязі (BORN_IN, PARTICIPATED_IN, RULED і г.д.)
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


class KnowledgeGraph:
    """
    Граф ведаў для гістарычных дадзеных
    
    Захоўвае сутнасці і сувязі паміж імі
    """
    
    def __init__(self):
        # Сутнасці па ID
        self.entities: Dict[str, Entity] = {}
        
        # Сувязі
        self.relations: List[Relation] = []
        
        # Індэксы для хуткага пошуку
        self.entity_by_name: Dict[str, str] = {}  # name -> id
        self.entities_by_type: Dict[str, Set[str]] = defaultdict(set)  # type -> ids
        
        # Сувязі па крыніцы і мэце
        self.outgoing_edges: Dict[str, List[Relation]] = defaultdict(list)
        self.incoming_edges: Dict[str, List[Relation]] = defaultdict(list)
        
        logger.info("✅ Граф ведаў ініцыялізаваны")
    
    def add_entity(self, entity_id: str, name: str, entity_type: str, 
                   metadata: Dict = None) -> Entity:
        """
        Дадаванне сутнасці ў граф
        
        Args:
            entity_id: унікальны ID
            name: назва сутнасці
            entity_type: тып (PERSON, LOCATION, і г.д.)
            metadata: дадатковая інфармацыя
            
        Returns:
            Створаная сутнасць
        """
        entity = Entity(
            id=entity_id,
            name=name,
            type=entity_type,
            metadata=metadata or {}
        )
        
        self.entities[entity_id] = entity
        self.entity_by_name[name.lower()] = entity_id
        self.entities_by_type[entity_type].add(entity_id)
        
        logger.debug(f"📝 Дададзена сутнасць: {name} ({entity_type})")
        return entity
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str,
                     confidence: float = 1.0, metadata: Dict = None) -> Relation:
        """
        Дадаванне сувязі паміж сутнасцямі
        
        Args:
            source_id: ID крыніцы
            target_id: ID мэты
            relation_type: тып сувязі
            confidence: упэўненасць (0-1)
            metadata: дадатковая інфармацыя
            
        Returns:
            Створаная сувязь
        """
        relation = Relation(
            source=source_id,
            target=target_id,
            type=relation_type,
            confidence=confidence,
            metadata=metadata or {}
        )
        
        self.relations.append(relation)
        self.outgoing_edges[source_id].append(relation)
        self.incoming_edges[target_id].append(relation)
        
        logger.debug(f"🔗 Дададзена сувязь: {source_id} -[{relation_type}]-> {target_id}")
        return relation
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Атрыманне сутнасці па ID"""
        return self.entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Атрыманне сутнасці па назве"""
        entity_id = self.entity_by_name.get(name.lower())
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def get_neighbors(self, entity_id: str, direction: str = "both",
                      relation_types: List[str] = None) -> List[Tuple[Entity, Relation]]:
        """
        Атрыманне суседніх сутнасцей
        
        Args:
            entity_id: ID сутнасці
            direction: "outgoing", "incoming", ці "both"
            relation_types: фільтр па тыпах сувязяў
            
        Returns:
            Спіс (сутнасць, сувязь)
        """
        neighbors = []
        
        if direction in ["outgoing", "both"]:
            for relation in self.outgoing_edges.get(entity_id, []):
                if relation_types and relation.type not in relation_types:
                    continue
                target_entity = self.entities.get(relation.target)
                if target_entity:
                    neighbors.append((target_entity, relation))
        
        if direction in ["incoming", "both"]:
            for relation in self.incoming_edges.get(entity_id, []):
                if relation_types and relation.type not in relation_types:
                    continue
                source_entity = self.entities.get(relation.source)
                if source_entity:
                    neighbors.append((source_entity, relation))
        
        return neighbors
    
    def find_path(self, source_id: str, target_id: str, 
                  max_depth: int = 3) -> Optional[List[Tuple[str, str]]]:
        """
        Пошук шляху паміж дзвюма сутнасцямі
        
        Args:
            source_id: ID пачатковай сутнасці
            target_id: ID канчатковай сутнасці
            max_depth: максімальная глыбіня пошуку
            
        Returns:
            Спіс (entity_id, relation_type) або None
        """
        from collections import deque
        
        queue = deque([(source_id, [])])
        visited = {source_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if len(path) >= max_depth:
                continue
            
            if current_id == target_id:
                return path
            
            # Пошук па выходных сувязях
            for relation in self.outgoing_edges.get(current_id, []):
                if relation.target not in visited:
                    visited.add(relation.target)
                    new_path = path + [(current_id, relation.type)]
                    queue.append((relation.target, new_path))
        
        return None
    
    def get_subgraph(self, entity_ids: Set[str], 
                     include_neighbors: bool = True) -> 'KnowledgeGraph':
        """
        Атрыманне падграфа
        
        Args:
            entity_ids: IDs сутнасцей для ўключэння
            include_neighbors: ці ўключаць суседзяў
            
        Returns:
            Новы граф з адбранымі сутнасцямі
        """
        subgraph = KnowledgeGraph()
        
        all_ids = set(entity_ids)
        
        if include_neighbors:
            for eid in entity_ids:
                for neighbor, _ in self.get_neighbors(eid):
                    all_ids.add(neighbor.id)
        
        # Капіраванне сутнасцей
        for eid in all_ids:
            entity = self.entities.get(eid)
            if entity:
                subgraph.add_entity(
                    entity.id, entity.name, entity.type, entity.metadata
                )
        
        # Капіраванне сувязяў
        for relation in self.relations:
            if relation.source in all_ids and relation.target in all_ids:
                subgraph.add_relation(
                    relation.source, relation.target, relation.type,
                    relation.confidence, relation.metadata
                )
        
        return subgraph
    
    def extract_entities_from_text(self, text: str) -> List[Entity]:
        """
        Вылучэнне сутнасцей з тэксту (просты варыянт)
        
        Для больш дакладнага вылучэння выкарыстоўвайце BelarusianNLP
        """
        import re
        
        entities = []
        
        # Даты
        for match in re.finditer(r'\b(\d{4})\b', text):
            year = match.group(1)
            entity_id = f"date_{year}"
            entities.append(self.add_entity(
                entity_id, year, "DATE", {'year': int(year)}
            ))
        
        # Уласныя назвы (спрашчона)
        for match in re.finditer(r'\b([А-ЯЁЎІ][а-яёўі\']+(?:\s+[А-ЯЁЎІ][а-яёўі\']+)*)\b', text):
            name = match.group(1)
            # Праверка на кароткія і частыя словы
            if len(name) > 4 and name not in ['Гэта', 'Такі', 'Сам', 'Які', 'Калі']:
                entity_id = f"person_{name.lower().replace(' ', '_')}"
                if entity_id not in self.entities:
                    entities.append(self.add_entity(
                        entity_id, name, "PERSON", {}
                    ))
        
        return entities
    
    def get_stats(self) -> Dict:
        """Статыстыка графа"""
        return {
            'total_entities': len(self.entities),
            'total_relations': len(self.relations),
            'entities_by_type': {k: len(v) for k, v in self.entities_by_type.items()},
            'avg_relations_per_entity': len(self.relations) / max(len(self.entities), 1)
        }
    
    def save(self, filepath: str):
        """Захаванне графа ў JSON"""
        data = {
            'entities': [
                {
                    'id': e.id,
                    'name': e.name,
                    'type': e.type,
                    'metadata': e.metadata
                }
                for e in self.entities.values()
            ],
            'relations': [
                {
                    'source': r.source,
                    'target': r.target,
                    'type': r.type,
                    'confidence': r.confidence,
                    'metadata': r.metadata
                }
                for r in self.relations
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Граф захаваны ў {filepath}")
    
    def load(self, filepath: str):
        """Загрузка графа з JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Ачышчэнне
        self.entities = {}
        self.relations = []
        self.entity_by_name = {}
        self.entities_by_type = defaultdict(set)
        self.outgoing_edges = defaultdict(list)
        self.incoming_edges = defaultdict(list)
        
        # Загрузка сутнасцей
        for e_data in data.get('entities', []):
            self.add_entity(
                e_data['id'], e_data['name'], e_data['type'], e_data.get('metadata')
            )
        
        # Загрузка сувязяў
        for r_data in data.get('relations', []):
            self.add_relation(
                r_data['source'], r_data['target'], r_data['type'],
                r_data.get('confidence', 1.0), r_data.get('metadata')
            )
        
        logger.info(f"📥 Граф загружаны з {filepath}")


class GraphRAG:
    """
    GraphRAG - камбінаванне графа ведаў з вектарным пошукам
    """
    
    def __init__(self, knowledge_graph: KnowledgeGraph = None):
        """
        Ініцыялізацыя GraphRAG
        
        Args:
            knowledge_graph: граф ведаў
        """
        self.kg = knowledge_graph or KnowledgeGraph()
        
        logger.info("✅ GraphRAG ініцыялізаваны")
    
    def query(self, question: str, use_graph: bool = True,
              use_vector: bool = True) -> Dict:
        """
        Адказ на пытанне з выкарыстаннем графа і/або вектарнага пошуку
        
        Args:
            question: пытанне карыстальніка
            use_graph: ці выкарыстоўваць граф
            use_vector: ці выкарыстоўваць вектарны пошук
            
        Returns:
            Dict з адказам і крыніцамі
        """
        results = {
            'answer': '',
            'entities_found': [],
            'relations_found': [],
            'paths': []
        }
        
        # Вылучэнне сутнасцей з пытання
        entities_in_question = self.kg.extract_entities_from_text(question)
        
        if use_graph:
            # Пошук сувязяў паміж знойдзенымі сутнасцямі
            for i, entity1 in enumerate(entities_in_question):
                for entity2 in entities_in_question[i+1:]:
                    path = self.kg.find_path(entity1.id, entity2.id)
                    if path:
                        results['paths'].append({
                            'from': entity1.name,
                            'to': entity2.name,
                            'path': path
                        })
                
                # Атрыманне суседзяў
                neighbors = self.kg.get_neighbors(entity1.id)
                for neighbor, relation in neighbors[:5]:  # Top 5
                    results['entities_found'].append({
                        'entity': neighbor.name,
                        'type': neighbor.type,
                        'relation': relation.type
                    })
                    results['relations_found'].append({
                        'source': entity1.name,
                        'target': neighbor.name,
                        'type': relation.type
                    })
        
        # Фарміраванне адказу
        if results['paths']:
            paths_str = "; ".join(
                f"{p['from']} → {p['to']} ({len(p['path'])} крокаў)"
                for p in results['paths'][:3]
            )
            results['answer'] = f"Знойдзены сувязі: {paths_str}"
        elif results['entities_found']:
            entities_str = ", ".join(
                f"{e['entity']} ({e['relation']})"
                for e in results['entities_found'][:5]
            )
            results['answer'] = f"Знойдзены сутнасці: {entities_str}"
        else:
            results['answer'] = "Сувязі не знойдзены. Паспрабуйце вектарны пошук."
        
        return results
    
    def build_from_facts(self, facts: List[Dict]):
        """
        Пабудова графа з спісу фактаў
        
        Args:
            facts: спіс фактаў з метаданымі
        """
        logger.info(f"🏗️ Пабудова графа з {len(facts)} фактаў...")
        
        for fact in facts:
            fact_text = fact.get('fact', '')
            
            # Вылучэнне сутнасцей
            entities = self.kg.extract_entities_from_text(fact_text)
            
            # Стварэнне сувязяў паміж усімі сутнасцямі ў факце
            entity_ids = [e.id for e in entities]
            for i, eid1 in enumerate(entity_ids):
                for eid2 in entity_ids[i+1:]:
                    self.kg.add_relation(
                        eid1, eid2, "RELATED_TO", 
                        metadata={'source_fact': fact_text}
                    )
        
        stats = self.kg.get_stats()
        logger.info(f"✅ Граф пабудаваны: {stats['total_entities']} сутнасцей, "
                   f"{stats['total_relations']} сувязяў")


def main():
    """Тэставанне графа ведаў"""
    print("="*80)
    print("🧪 ТЭСТАВАННЕ GRAPH RAG")
    print("="*80)
    
    # Стварэнне графа
    kg = KnowledgeGraph()
    
    # Дадаванне сутнасцей
    kg.add_entity("person_kalinouski", "Кастусь Каліноўскі", "PERSON")
    kg.add_entity("date_1838", "1838", "DATE", {'year': 1838})
    kg.add_entity("location_mastaulyany", "Мастаўляны", "LOCATION")
    kg.add_entity("event_uprising_1863", "Паўстанне 1863 года", "EVENT")
    kg.add_entity("date_1864", "1864", "DATE", {'year': 1864})
    kg.add_entity("location_vilnia", "Вільня", "LOCATION")
    
    # Дадаванне сувязяў
    kg.add_relation("person_kalinouski", "date_1838", "BORN_IN")
    kg.add_relation("person_kalinouski", "location_mastaulyany", "BORN_IN")
    kg.add_relation("person_kalinouski", "event_uprising_1863", "LED")
    kg.add_relation("person_kalinouski", "date_1864", "DIED_IN")
    kg.add_relation("person_kalinouski", "location_vilnia", "DIED_IN")
    
    # Статыстыка
    print("\n📊 Статыстыка графа:")
    stats = kg.get_stats()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    # Пошук шляху
    print("\n🔍 Пошук шляху:")
    path = kg.find_path("person_kalinouski", "location_vilnia")
    if path:
        print(f"  Шлях знойдзены: {path}")
    
    # Суседзі
    print("\n🔗 Суседзі Кастуся Каліноўскага:")
    neighbors = kg.get_neighbors("person_kalinouski")
    for entity, relation in neighbors:
        print(f"  • {entity.name} ({entity.type}) ← [{relation.type}]")
    
    # GraphRAG
    print("\n🤖 GraphRAG запыт:")
    graph_rag = GraphRAG(kg)
    result = graph_rag.query("Дзе нарадзіўся Кастусь Каліноўскі?")
    
    print(f"  Адказ: {result['answer']}")
    print(f"  Сутнасці: {result['entities_found'][:3]}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
