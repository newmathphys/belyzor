"""
БелУзор v2026: GraphRAG - Граф ведаў для гістарычных сувязей

Інтэграцыя:
- Neo4j для захавання графа
- Extract Entities and Relations з тэксту
- Адказы на складаныя пытанні праз шляхі ў графе
"""

import os
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️ Neo4j driver не ўсталяваны. Граф ведаў будзе працаваць у рэжыме імітацыі.")


class RelationType(Enum):
    """Тыпы адносін у графе ведаў."""
    BORN_IN = "BORN_IN"  # Нарадзіўся ў
    DIED_IN = "DIED_IN"  # Памёр у
    LIVED_IN = "LIVED_IN"  # Жыў у
    CREATED = "CREATED"  # Стварыў
    PARTICIPATED_IN = "PARTICIPATED_IN"  # Удзельнічаў у
    RULED = "RULED"  # Кіраваў
    ALLIED_WITH = "ALLIED_WITH"  # Саюзнік
    FOUGHT_AGAINST = "FOUGHT_AGAINST"  # Змагаўся супраць
    PUBLISHED = "PUBLISHED"  # Апублікаваў
    WROTE = "WROTE"  # Напісаў
    ESTABLISHED = "ESTABLISHED"  # Заснаваў
    OCCURRED_IN = "OCCURRED_IN"  # Адбылося ў
    OCCURRED_AT = "OCCURRED_AT"  # Адбылося ў год


@dataclass
class Entity:
    """Сутнасць у графе."""
    id: str
    entity_type: str
    name: str
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class Relation:
    """Адносіна паміж сутнасцямі."""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class KnowledgeGraph:
    """Граф ведаў для гістарычных дадзеных."""
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password"
    ):
        """
        Ініцыялізацыя графа ведаў.
        
        Args:
            neo4j_uri: URI да Neo4j сервера
            neo4j_user: Карыстальнік
            neo4j_password: Пароль
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        self.driver = None
        self.use_neo4j = NEO4J_AVAILABLE
        
        if self.use_neo4j:
            try:
                print(f"🔗 Падключэнне да Neo4j: {neo4j_uri}...")
                self.driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                
                # Праверка падключэння
                with self.driver.session() as session:
                    session.run("MATCH (n) RETURN count(n) as count")
                
                print("✅ Neo4j падключаны")
                
                # Стварэнне індэксаў
                self._create_indexes()
                
            except Exception as e:
                print(f"⚠️ Памылка падключэння да Neo4j: {e}")
                print("🔄 Пераход у рэжым імітацыі (in-memory)")
                self.use_neo4j = False
        
        # In-memory граф для рэжыму імітацыі
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
    
    def _create_indexes(self):
        """Стварэнне індэксаў для аптымізацыі."""
        if not self.use_neo4j or not self.driver:
            return
        
        with self.driver.session() as session:
            # Індэкс па імёнах
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            # Індэкс па тыпах
            session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")
    
    def add_entity(self, entity: Entity):
        """
        Даданне сутнасці ў граф.
        
        Args:
            entity: Сутнасць для дадання
        """
        if self.use_neo4j and self.driver:
            with self.driver.session() as session:
                session.run("""
                    MERGE (e:Entity {id: $id})
                    SET e.name = $name,
                        e.type = $entity_type,
                        e.properties = $properties
                """,
                id=entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                properties=entity.properties
                )
        else:
            # In-memory
            self.entities[entity.id] = entity
    
    def add_relation(self, relation: Relation):
        """
        Даданне адносіны паміж сутнасцямі.
        
        Args:
            relation: Адносіна для дадання
        """
        if self.use_neo4j and self.driver:
            with self.driver.session() as session:
                session.run("""
                    MATCH (a:Entity {id: $source_id})
                    MATCH (b:Entity {id: $target_id})
                    MERGE (a)-[r:RELATION {type: $relation_type}]->(b)
                    SET r.properties = $properties
                """,
                source_id=relation.source_id,
                target_id=relation.target_id,
                relation_type=relation.relation_type.value,
                properties=relation.properties
                )
        else:
            # In-memory
            self.relations.append(relation)
    
    def extract_and_add_from_text(self, text: str, source: str = "unknown"):
        """
        Выдзяленне сутнасцей і адносін з тэксту і даданне ў граф.
        
        Args:
            text: Тэкст для аналізу
            source: Крыніца тэксту
        """
        # Простая эврыстыка для прыкладу
        # У рэальнасці трэба выкарыстоўваць LLM або спецыялізаваныя мадэлі
        
        entities_added = []
        relations_added = []
        
        # Прыклад: пошук вядомых асоб і месцаў
        import re
        
        # Пошук імён
        person_pattern = r'\b(Францыск\s+Скарына|Леў\s+Сапега|Вітаўт|Ягайла)\b'
        for match in re.finditer(person_pattern, text):
            name = match.group()
            entity_id = f"person_{name.replace(' ', '_').lower()}"
            
            entity = Entity(
                id=entity_id,
                entity_type="PERSON",
                name=name,
                properties={"source": source}
            )
            self.add_entity(entity)
            entities_added.append(entity)
        
        # Пошук гарадоў
        location_pattern = r'\b(Полацк|Менск|Вільня|Гродна)\b'
        for match in re.finditer(location_pattern, text):
            name = match.group()
            entity_id = f"location_{name.lower()}"
            
            entity = Entity(
                id=entity_id,
                entity_type="LOCATION",
                name=name,
                properties={"source": source}
            )
            self.add_entity(entity)
            entities_added.append(entity)
        
        # Пошук дат
        date_pattern = r'\b(\d{4})\s+год'
        for match in re.finditer(date_pattern, text):
            year = match.group(1)
            entity_id = f"year_{year}"
            
            entity = Entity(
                id=entity_id,
                entity_type="DATE",
                name=year,
                properties={"source": source}
            )
            self.add_entity(entity)
            entities_added.append(entity)
        
        # Стварэнне простых адносін (эврыстыка)
        if len(entities_added) >= 2:
            # Калі ёсць асоба і месца - ствараем BORN_IN або LIVED_IN
            persons = [e for e in entities_added if e.entity_type == "PERSON"]
            locations = [e for e in entities_added if e.entity_type == "LOCATION"]
            
            for person in persons:
                for location in locations[:1]:  # Першае месца
                    relation = Relation(
                        source_id=person.id,
                        target_id=location.id,
                        relation_type=RelationType.LIVED_IN,
                        properties={"source": source}
                    )
                    self.add_relation(relation)
                    relations_added.append(relation)
        
        return entities_added, relations_added
    
    def query_path(
        self,
        source_entity: str,
        target_entity: str,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Пошук шляху паміж дзвюма сутнасцямі.
        
        Args:
            source_entity: ID пачатковай сутнасці
            target_entity: ID канчатковай сутнасці
            max_depth: Максімальная глыбіня пошуку
            
        Returns:
            Спіс шляхоў
        """
        if self.use_neo4j and self.driver:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (start:Entity {id: $source})-[*1..$max_depth]-(end:Entity {id: $target})
                    RETURN path, length(path) as len
                    ORDER BY len
                    LIMIT 5
                """,
                source=source_entity,
                target=target_entity,
                max_depth=max_depth
                )
                
                paths = []
                for record in result:
                    path_data = {
                        "length": record["len"],
                        "nodes": [],
                        "relationships": []
                    }
                    
                    # Апрацоўка вузлоў
                    for node in record["path"].nodes:
                        path_data["nodes"].append({
                            "id": node["id"],
                            "name": node["name"],
                            "type": node["type"]
                        })
                    
                    # Апрацоўка адносін
                    for rel in record["path"].relationships:
                        path_data["relationships"].append({
                            "type": rel["type"],
                            "properties": rel.get("properties", {})
                        })
                    
                    paths.append(path_data)
                
                return paths
        else:
            # In-memory: просты пошук
            return self._find_path_in_memory(source_entity, target_entity, max_depth)
    
    def _find_path_in_memory(
        self,
        source_id: str,
        target_id: str,
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """Пошук шляху ў in-memory графе."""
        # BFS пошук
        from collections import deque
        
        visited = set()
        queue = deque([(source_id, [])])
        paths = []
        
        while queue and len(paths) < 5:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                # Знойдзены шлях
                path_nodes = [self.entities.get(pid) for pid in path + [current_id] if pid in self.entities]
                paths.append({
                    "length": len(path),
                    "nodes": [
                        {"id": n.id, "name": n.name, "type": n.entity_type}
                        for n in path_nodes if n
                    ],
                    "relationships": []
                })
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Пошук суседзяў
            for rel in self.relations:
                neighbor_id = None
                if rel.source_id == current_id:
                    neighbor_id = rel.target_id
                elif rel.target_id == current_id:
                    neighbor_id = rel.source_id
                
                if neighbor_id and neighbor_id not in visited:
                    queue.append((neighbor_id, path + [current_id]))
        
        return paths
    
    def get_related_entities(
        self,
        entity_id: str,
        relation_types: Optional[List[RelationType]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Атрыманне звязаных сутнасцей.
        
        Args:
            entity_id: ID сутнасці
            relation_types: Фільтр па тыпах адносін
            limit: Ліміт вынікаў
            
        Returns:
            Спіс звязаных сутнасцей
        """
        if self.use_neo4j and self.driver:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {id: $id})-[r]-(related:Entity)
                    WHERE $relation_types IS NULL OR r.type IN $relation_types
                    RETURN related, r.type as relation_type
                    LIMIT $limit
                """,
                id=entity_id,
                relation_types=[rt.value for rt in relation_types] if relation_types else None,
                limit=limit
                )
                
                related = []
                for record in result:
                    node = record["related"]
                    related.append({
                        "id": node["id"],
                        "name": node["name"],
                        "type": node["type"],
                        "relation": record["relation_type"]
                    })
                
                return related
        else:
            # In-memory
            related = []
            for rel in self.relations[:limit]:
                if rel.source_id == entity_id or rel.target_id == entity_id:
                    if relation_types is None or rel.relation_type in relation_types:
                        other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
                        if other_id in self.entities:
                            other = self.entities[other_id]
                            related.append({
                                "id": other.id,
                                "name": other.name,
                                "type": other.entity_type,
                                "relation": rel.relation_type.value
                            })
            return related
    
    def get_stats(self) -> Dict[str, Any]:
        """Атрыманне статыстыкі графа."""
        if self.use_neo4j and self.driver:
            with self.driver.session() as session:
                entity_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
                relation_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
                
                return {
                    "entities": entity_count,
                    "relations": relation_count,
                    "mode": "neo4j"
                }
        else:
            return {
                "entities": len(self.entities),
                "relations": len(self.relations),
                "mode": "in-memory"
            }
    
    def close(self):
        """Закрыццё падключэння."""
        if self.driver:
            self.driver.close()


def main():
    """Прыклад выкарыстання графа ведаў."""
    # Ініцыялізацыя
    graph = KnowledgeGraph(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password"
    )
    
    # Даданне сутнасцей
    print("\n➕ Даданне сутнасцей...")
    
    entities = [
        Entity(id="person_skaryna", entity_type="PERSON", name="Францыск Скарына"),
        Entity(id="person_sapega", entity_type="PERSON", name="Леў Сапега"),
        Entity(id="location_polatsk", entity_type="LOCATION", name="Полацк"),
        Entity(id="location_vilnya", entity_type="LOCATION", name="Вільня"),
        Entity(id="year_1517", entity_type="DATE", name="1517"),
        Entity(id="year_1588", entity_type="DATE", name="1588"),
    ]
    
    for entity in entities:
        graph.add_entity(entity)
    
    # Даданне адносін
    print("➕ Даданне адносін...")
    
    relations = [
        Relation("person_skaryna", "location_polatsk", RelationType.BORN_IN),
        Relation("person_skaryna", "year_1517", RelationType.PUBLISHED),
        Relation("person_sapega", "year_1588", RelationType.CREATED),
        Relation("person_sapega", "location_vilnya", RelationType.LIVED_IN),
    ]
    
    for rel in relations:
        graph.add_relation(rel)
    
    # Статыстыка
    print("\n📊 Статыстыка графа:")
    stats = graph.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Запыт шляху
    print("\n🔍 Пошук шляху паміж Скарынам і Вільняй:")
    paths = graph.query_path("person_skaryna", "location_vilnya", max_depth=3)
    
    for i, path in enumerate(paths, 1):
        print(f"\nШлях {i} (даўжыня: {path['length']}):")
        for node in path['nodes']:
            print(f"  → {node['name']} ({node['type']})")
    
    # Звязаныя сутнасці
    print("\n🔗 Звязаныя сутнасці для Скарыны:")
    related = graph.get_related_entities("person_skaryna")
    
    for item in related:
        print(f"  {item['name']} ({item['type']}) — {item['relation']}")
    
    # Выдзяленне з тэксту
    print("\n📝 Выдзяленне з тэксту:")
    text = "Францыск Скарына нарадзіўся ў Полацку і выдаў Біблію ў 1517 годзе."
    ents, rels = graph.extract_and_add_from_text(text, source="test")
    
    print(f"  Знойдзена сутнасцей: {len(ents)}")
    print(f"  Знойдзена адносін: {len(rels)}")
    
    graph.close()


if __name__ == "__main__":
    main()
