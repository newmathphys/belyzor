# 🧠🇧🇾 БелУзор v0.1

**Інтэлектуальная пошукавая сістэма па гісторыі Беларусі**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces)

---

## 📖 Апісанне

**БелУзор** — гэта інтэлектуальная пошукавая сістэма, якая працуе па **ўзоры (кнізе)**, якому вы давяраеце.

Сістэма выкарыстоўвае:
- 🔍 **100,484 фактаў** з гісторыі Беларусі
- 📚 **18 тамоў энцыклапедыі**
- 📖 **8 школьных падручнікаў**
- 📗 **26 слоўнікаў**
- 🧠 **LLM інтэграцыю** (Ollama, LM Studio, OpenRouter)

---

## 🚀 Хуткі старт

### 1. Усталёўка

```bash
# Кланаванне рэпазіторыя
git clone https://github.com/newmathphys/belyzor.git
cd belyzor

# Усталёўка залежнасцей
pip install -r requirements.txt
```

### 2. Запуск вэб-інтэрфейсу

```bash
# Запуск
./run.sh web

# Адкрыць у браўзеры
http://localhost:5000
```

### 3. Запуск GUI (апцыянальна)

```bash
./run.sh gui
```

---

## 📋 Каманды

| Каманда | Апісанне |
|---------|----------|
| `./run.sh web` | Запуск вэб-інтэрфейсу |
| `./run.sh gui` | Запуск графічнага інтэрфейсу |
| `./run.sh run` | Кансольная версія |
| `./run.sh test` | Запуск тэстаў |
| `./run.sh books-list` | Спіс кніг |
| `./run.sh books-add <file>` | Дадаць кнігу |
| `./run.sh llm-on ollama` | Уключыць LLM |
| `./run.sh llm-status` | Статус LLM |

---

## 🌐 Hugging Face Spaces

### Размяшчэнне на Hugging Face:

1. Стварыце новы Space на [huggingface.co/spaces](https://huggingface.co/spaces)
2. Абярыце **Gradio** або **Docker**
3. Загрузіце файлы:
   ```bash
   git clone https://huggingface.co/spaces/newmathphys/belyzor
   cp -r * /path/to/huggingface/repo/
   git add .
   git commit -m "Initial commit"
   git push
   ```

### app.py для Hugging Face:

```python
# Гл. app.py (уключаны ў рэпазіторый)
```

---

## 📊 Метрыкі

| Метрыка | Значэнне |
|---------|----------|
| **Фактаў у базе** | 100,484 |
| **Індэксаваных слоў** | 347,517 |
| **Кніг** | 19 (8 падручнікаў + 11 томаў энцыклапедыі) |
| **Слоўнікаў** | 26 |
| **Час адказу** | ~10-30 мс (з кэшам) |
| **Тэсты** | 19/20 (95%) |

---

## 🏗️ Апісанне архітэктуры

```
belyzor/
├── src/
│   ├── core/
│   │   ├── ultimate_engine_v1.py    # Асноўны рухавік
│   │   ├── lemmatizer.py            # Лематызатар (з кэшам)
│   │   ├── llm_interface.py         # LLM інтэрфейс
│   │   ├── book_manager.py          # Кіраванне кнігамі
│   │   └── logger.py                # Лагаванне
│   ├── web/
│   │   ├── web_server.py            # Вэб-сервер (Flask)
│   │   ├── templates/
│   │   │   └── index.html           # Галоўная старонка
│   │   └── static/
│   │       ├── css/style.css        # Стылі
│   │       └── js/app.js            # JavaScript
│   └── gui/
│       └── gui_app.py               # Графічны інтэрфейс (PyQt5)
├── data/
│   ├── etalons/
│   │   └── facts.json               # Факты
│   └── raw/
│       ├── history/                 # Падручнікі
│       ├── bel-en/                  # Энцыклапедыі
│       └── dictionaries/            # Слоўнікі
├── tests/
│   └── test_system.py               # Аўтатэсты
├── requirements.txt
├── run.sh
└── README.md
```

---

## 🧪 Тэставанне

```bash
# Запуск тэстаў
./run.sh test

# Вынікі:
# Precision: 100%
# Recall: 85%
# F1-score: 90.17%
```

---

## 🔧 Канфігурацыя

### llm_config.json

```json
{
  "enabled": false,
  "provider": "ollama",
  "model": "llama3.2:3b",
  "api_key": "",
  "max_tokens": 1000,
  "temperature": 0.5,
  "endpoints": {
    "ollama": "http://localhost:11434",
    "lmstudio": "http://localhost:1234/v1",
    "openrouter": "https://openrouter.ai/api/v1"
  },
  "custom_endpoint": "http://192.168.0.116:1234/v1",
  "use_custom_endpoint": false
}
```

---

## 🛠️ Распрацоўка

### Усталёўка для распрацоўкі

```bash
# Стварэнне virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# або
venv\Scripts\activate  # Windows

# Усталёўка залежнасцей
pip install -r requirements.txt

# Запуск тэстаў
./run.sh test
```

---

## 📄 Ліцэнзія

MIT License — глядзіце [LICENSE](LICENSE)

---

## 👥 Аўтары

**БелУзор v0.1 Team**

---

## 📞 Кантакты

- **Issues:** https://github.com/newmathphys/belyzor/issues
- **Hugging Face:** https://huggingface.co/spaces/newmathphys/belyzor

---

## 🎯 Планы

- [ ] Дадаць больш фактаў
- [ ] Палепшыць лематызацыю
- [ ] Інтэграцыя з API
- [ ] Вэб-інтэрфейс
- [ ] Мабільная версія

---

**Made with ❤️ for Belarus**
