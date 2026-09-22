# 🧠 БЕЛУЗОР v2026 — Архітэктура і Інструкцыі

## Агляд

**БелУзор v2026** — гэта мадэрнізаваная інтэлектуальная пошукавая сістэма па гісторыі Беларусі з выкарыстаннем перадавых тэхналогій 2026 года:

- **Гібрыдны пошук** (Dense + Sparse) з RRF алгарытмам
- **Вектарныя эмбеддінгі** (BGE-M3, multilingual-E5)
- **NLP апрацоўка** беларускага тэксту (Stanza/SpaCy)
- **Рэранжыраванне** фактаў (BGE-Reranker)
- **Граф ведаў** (GraphRAG) для складаных запытаў
- **Сэмплінг тэксту** на сэнсавыя часткі

---

## 📁 Структура праекта

```
/workspace
├── src/
│   └── core/
│       ├── ultimate_engine_v1.py    # Асноўны рухавік (сумяшчальнасць)
│       ├── lemmatizer.py            # Лематызацыя беларускай мовы
│       ├── llm_interface.py         # Інтэрфейс да LLM
│       ├── book_manager.py          # Кіраванне кнігамі
│       ├── logger.py                # Сістэма лагавання
│       │
│       ├── vector_db/               # Вектарная база дадзеных (НОВАЕ)
│       │   ├── __init__.py
│       │   ├── vector_store.py      # VectorDatabase, RRF пошук
│       │   └── chroma_impl.py       # ChromaDB інтэграцыя
│       │
│       ├── nlp/                     # NLP апрацоўка (НОВАЕ)
│       │   ├── __init__.py
│       │   ├── embeddings.py        # BGE-M3, E5 эмбеддінгі
│       │   ├── belarusian_nlp.py    # Stanza/SpaCy для беларускай
│       │   └── semantic_chunking.py # Сэмплінг тэксту
│       │
│       ├── reranker/                # Рэранжыраванне (НОВАЕ)
│       │   ├── __init__.py
│       │   └── reranker.py          # BGE-Reranker, Cross-Encoder
│       │
│       └── graph_rag/               # Граф ведаў (НОВАЕ)
│           ├── __init__.py
│           └── knowledge_graph.py   # KnowledgeGraph, GraphRAG
│
├── data/
│   ├── etalons/
│   │   └── facts.json              # Факты з базы
│   └── vector_db/                  # Вектарная БД (ствараецца)
│
├── requirements.txt                 # Залежнасці (абноўлены)
└── README_ADVANCED.md              # Гэты файл
```

---

## 🚀 Хуткі старт

### 1. Устаноўка залежнасцей

```bash
cd /workspace
pip install -r requirements.txt
```

### 2. Тэставанне кампанентаў

#### Вектарная база дадзеных:
```bash
python src/core/vector_db/vector_store.py
```

#### Эмбеддінгі і чанкінг:
```bash
python src/core/nlp/embeddings.py
```

#### NLP апрацоўка:
```bash
python src/core/nlp/belarusian_nlp.py
```

#### Рэранжыраванне:
```bash
python src/core/reranker/reranker.py
```

#### Граф ведаў:
```bash
python src/core/graph_rag/knowledge_graph.py
```

---

## 🏗️ Архітэктура

### 1. Гібрыдны пошук (Hybrid Search)

```
Запыт карыстальніка
       │
       ├─────────────┬──────────────┐
       ▼             ▼              ▼
   Dense Search  Sparse Search   Graph Query
   (вектары)     (BM25/TF-IDF)   (сутнасці)
       │             │              │
       └─────────────┴──────────────┘
                   ▼
           RRF Fusion Algorithm
                   ▼
           Рэранжыраванне
           (BGE-Reranker)
                   ▼
              LLM + RAG
              (адказ)
```

### 2. Кампаненты

#### Вектарная база дадзеных (`vector_store.py`)
- **Dense Retrieval**: Пошук па вектарных укладаннях
- **Sparse Retrieval**: Традыцыйны BM25/TF-IDF
- **RRF (Reciprocal Rank Fusion)**: Аб'яднанне вынікаў
- **Фільтрацыя**: Па метаданых (крыніца, год, тып)

#### Эмбеддінгі (`embeddings.py`)
- **Мадэлі**: BAAI/bge-m3, intfloat/multilingual-e5
- **Query/Document**: Розныя прэфіксы для лепшага пошуку
- **Semantic Chunking**: Разбіццё тэксту па сэнсе
- **Кэш**: Для хуткасці

#### NLP (`belarusian_nlp.py`)
- **Stanza**: Stanford NLP для беларускай мовы
- **NER**: Вылучэнне асоб, месцаў, дат
- **Лематызацыя**: З улікам кантэксту
- **Марфалогія**: Часціны мовы, сінтаксіс

#### Рэранжыраванне (`reranker.py`)
- **Cross-Encoder**: Дакладная ацэнка рэлевантнасці
- **Top-K**: Адбор лепшых 5 фактаў для LLM
- **Ансамбль**: Некалькі мадэляў для дакладнасці

#### Граф ведаў (`knowledge_graph.py`)
- **Сутнасці**: PERSON, LOCATION, EVENT, DATE
- **Сувязі**: BORN_IN, LED, DIED_IN, RELATED_TO
- **GraphRAG**: Пошук шляхоў паміж сутнасцямі
- **Інтэграцыя**: З вектарным пошукам

---

## 📖 Прыклады выкарыстання

### 1. Вектарны пошук

```python
from src.core.vector_db import VectorDatabase
from src.core.nlp import EmbeddingModel

# Ініцыялізацыя
db = VectorDatabase(db_type="memory")
embedder = EmbeddingModel(model_name="BAAI/bge-m3")

# Загрузка фактаў
db.load_facts_from_json("data/etalons/facts.json")

# Пошук
query = "Калі нарадзіўся Кастусь Каліноўскі?"
query_embedding = embedder.encode_query(query)

results = db.hybrid_search(
    query_embedding=query_embedding,
    query_text=query,
    top_k=10,
    alpha=0.5  # Баланс паміж dense і sparse
)

for chunk_id, score in results:
    chunk = db.get_chunk(chunk_id)
    print(f"[{score:.3f}] {chunk.text}")
```

### 2. Рэранжыраванне

```python
from src.core.reranker import Reranker

reranker = Reranker(model_name="BAAI/bge-reranker-v2-m3")

query = "Хто кіраваў паўстаннем 1863 года?"
documents = [
    "Газета «Мужыцкая праўда» выдавалася ў 1863 годзе.",
    "Кастусь Каліноўскі нарадзіўся ў 1838 годзе.",
    "Паўстанне 1863 года кіраваў Кастусь Каліноўскі.",
    "Вітаўт Вялікі князь літоўскі ў 1392-1430 гадах.",
]

ranked = reranker.rerank(query, documents, top_k=3)

for doc, score in ranked:
    print(f"[{score:.3f}] {doc}")
```

### 3. NLP апрацоўка

```python
from src.core.nlp import BelarusianNLP

nlp = BelarusianNLP(backend="stanza")

text = "Кастусь Каліноўскі нарадзіўся ў 1838 годзе ў вёсцы Мастаўляны."

# Токенізацыя і лематызацыя
tokens = nlp.process(text)
for token in tokens:
    print(f"{token.text} → {token.lemma} [{token.pos}]")

# Вылучэнне сутнасцей
entities = nlp.extract_entities(text)
for entity in entities:
    print(f"[{entity.type}] {entity.text}")
```

### 4. Граф ведаў

```python
from src.core.graph_rag import KnowledgeGraph, GraphRAG

kg = KnowledgeGraph()

# Дадаванне сутнасцей
kg.add_entity("person_kalinouski", "Кастусь Каліноўскі", "PERSON")
kg.add_entity("date_1838", "1838", "DATE")
kg.add_relation("person_kalinouski", "date_1838", "BORN_IN")

# GraphRAG запыт
graph_rag = GraphRAG(kg)
result = graph_rag.query("Дзе нарадзіўся Кастусь Каліноўскі?")

print(result['answer'])
print(result['entities_found'])
```

---

## 🔧 Канфігурацыя

### Мадэлі эмбеддінгаў

```python
# Лепшыя для беларускай мовы
EMBEDDING_MODELS = {
    'best': 'BAAI/bge-m3',           # 1024 dim, падтрымка 8k токенаў
    'fast': 'intfloat/multilingual-e5-base',  # 768 dim
    'large': 'intfloat/multilingual-e5-large' # 1024 dim
}
```

### Рэранжыраванне

```python
RERANKER_MODELS = {
    'best': 'BAAI/bge-reranker-v2-m3',  # Лепшы для славянскіх
    'fast': 'BAAI/bge-reranker-base',
}
```

### Гібрыдны пошук

```python
# Баланс паміж Dense і Sparse
HYBRID_ALPHA = 0.5  # 0.5 = роўная вага
# > 0.5 = больш вектарнага пошуку
# < 0.5 = больш ключавых слоў
```

---

## 📊 Метрыкі

### Чакальныя паляпшэнні

| Метрыка | v0.1 (TF-IDF) | v2026 (Hybrid) |
|---------|---------------|----------------|
| Precision@5 | 0.65 | **0.85+** |
| Recall@10 | 0.70 | **0.90+** |
| MRR | 0.60 | **0.82+** |
| F1-Score | 0.67 | **0.87+** |

---

## 🎯 Наступныя крокі

1. **Інтэграцыя з асноўным рухавіком** (`ultimate_engine_v1.py`)
2. **Стварэнне FastAPI endpoint** для вэб-інтэрфейсу
3. **Кантэйнерызацыя** (Docker + Kubernetes)
4. **Маніторынг** (Prometheus + Grafana)
5. **Fine-tuning** мадэляў на беларускіх гістарычных тэкстах

---

## 📚 Літаратура

- [BGE-M3 Paper](https://arxiv.org/abs/2310.07554)
- [GraphRAG (Microsoft)](https://www.microsoft.com/en-us/research/project/graphrag/)
- [Stanza (Stanford NLP)](https://stanfordnlp.github.io/stanza/)
- [Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)

---

## ⚠️ Заўвагі

- Для працы з вялікімі мадэлямі патрэбна GPU (CUDA)
- Першы запуск запатрабуе загрузку мадэляў (~2-5 GB)
- Для прадукшн рэкамендуецца Qdrant замест in-memory базы

---

**Версія**: v2026.1  
**Дата**: Студзень 2026  
**Статус**: Гатова да тэставання
