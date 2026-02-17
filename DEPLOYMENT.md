# 📦 ІНСТРУКЦЫЯ ПА ЗАГРУЗЦЫ НА GITHUB І HUGGING FACE

## 🎯 Падрыхтоўка

### 1. Стварыце GitHub акаўнт

Калі яшчэ няма:
1. Адкрыйце https://github.com
2. Націсніце "Sign up"
3. Запоўніце форму

---

## 📤 ЗАГРУЗКА НА GITHUB

### Крок 1: Ініцыялізацыя рэпазіторыя

```bash
cd /home/mrbritneyxxx/belyzor-2

# Ініцыялізацыя git
git init

# Дадаванне ўсіх файлаў
git add .

# Першы каміт
git commit -m "✅ БелУзор v0.1 - Інтэлектуальная пошукавая сістэма"
```

### Крок 2: Стварэнне рэпазіторыя на GitHub

1. Адкрыйце https://github.com/new
2. Запоўніце:
   - **Repository name:** `belyzor`
   - **Description:** "Інтэлектуальная пошукавая сістэма па гісторыі Беларусі"
   - **Public:** ✅
   - **Initialize:** ❌ (не ставіць!)
3. Націсніце "Create repository"

### Крок 3: Прывязка і загрузка

```bash
# Прывязка да аддаленага рэпазіторыя
git remote add origin https://github.com/newmathphys/belyzor.git

# Загрузка
git branch -M main
git push -u origin main
```

**Гатова!** ✅

---

## 🤗 ЗАГРУЗКА НА HUGGING FACE SPACES

### Крок 1: Стварыце Hugging Face акаўнт

1. Адкрыйце https://huggingface.co/join
2. Запоўніце форму
3. Пацвердзіце email

### Крок 2: Стварыце новы Space

1. Адкрыйце https://huggingface.co/new-space
2. Запоўніце:
   - **Space name:** `belyzor`
   - **License:** MIT
   - **Space SDK:** **Gradio**
   - **Visibility:** Public
3. Націсніце "Create Space"

### Крок 3: Спампуйце рэпазіторый Space

```bash
# Замяніце newmathphys на ваш лагін
cd ~
git clone https://huggingface.co/spaces/newmathphys/belyzor
cd belyzor
```

### Крок 4: Скапіюйце файлы праекта

```bash
# Капіяванне файлаў з праекта
cp /home/mrbritneyxxx/belyzor-2/app.py .
cp /home/mrbritneyxxx/belyzor-2/requirements.txt .
cp -r /home/mrbritneyxxx/belyzor-2/src .
cp -r /home/mrbritneyxxx/belyzor-2/data .

# Заўвага: Вялікія файлы лепш не капіяваць!
# Яны ўжо ёсць у .gitignore
```

### Крок 5: Стварыце README для Space

```bash
cat > README.md << 'EOF'
---
title: БелУзор v0.1
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: gradio
pinned: false
license: mit
---

# 🧠🇧🇾 БелУзор v0.1

**Інтэлектуальная пошукавая сістэма па гісторыі Беларусі**

## Як карыстацца:

1. Увядзіце пытанне
2. Націсніце "🔍 Пошук"
3. Атрымайце адказ з крыніцамі

## Прыклады пытанняў:

- Год заснавання Мінска?
- Хто такі Кастусь Каліноўскі?
- Што такое Статут 1588 года?
- Грунвальдская бітва 1410 года

## Асаблівасці:

- ✅ 100,484 фактаў
- ✅ 18 тамоў энцыклапедыі
- ✅ 26 слоўнікаў
- ✅ LLM інтэграцыя

## Ліцэнзія: MIT
EOF
```

### Крок 6: Загрузка на Hugging Face

```bash
# Праверка што скапіявалася
ls -la

# Павінны быць:
# - app.py
# - requirements.txt
# - src/
# - data/ (часткова)
# - README.md

# Загрузка
git add .
git commit -m "✅ БелУзор v0.1 для Hugging Face"
git push
```

### Крок 7: Чакаем разгортвання

1. Адкрыйце ваш Space: `https://huggingface.co/spaces/newmathphys/belyzor`
2. Чакайце ~2-5 хвілін
3. Калі з'явіцца "Running" - гатова! ✅

---

## ⚙️ НАЛАДЫ

### .gitignore (ужо створаны)

Не загружае:
- ❌ Вялікія файлы дадзеных
- ❌ Логаў
- ❌ llm_config.json (можа ўтрымліваць ключы)
- ❌ __pycache__/

### requirements.txt

Ужо ўключаны:
- ✅ numpy
- ✅ Flask
- ✅ flask-cors
- ✅ gradio (для Hugging Face)
- ✅ PyQt5 (апцыянальна)

---

## 🔧 ВЫРАШЭННЕ ПРАБЛЕМ

### Праблема: Git не ўсталяваны

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install git

# Fedora
sudo dnf install git
```

### Праблема: Вялікія файлы

Калі файлы занадта вялікія (>100MB):

```bash
# Выдаліць з git
git rm --cached data/raw/bel-en/*.txt

# Дадаць у .gitignore
echo "data/raw/bel-en/*.txt" >> .gitignore

# Каміт
git commit -m "Выдаленне вялікіх файлаў"
```

### Праблема: Hugging Face не запускаецца

1. Праверце `app.py` - павінен быць у корані
2. Праверце `requirements.txt` - павінен мець gradio
3. Адкрыйце "Settings" → "Factory rebuild"

---

## 📊 СТРУКТУРА ПРАЕКТА

```
belyzor/
├── app.py                          # ✅ Галоўны файл для HF
├── requirements.txt                # ✅ Залежнасці
├── README.md                       # ✅ Апісанне
├── .gitignore                      # ✅ Ігнаруемыя файлы
├── src/                            # ✅ Код
│   ├── core/
│   ├── web/
│   └── gui/
├── data/                           # ⚠️ Часткова (вялікія файлы ў .gitignore)
│   ├── etalons/facts.json
│   └── raw/
└── tests/                          # ✅ Тэсты
```

---

## ✅ ПАСЛЯ ЗАГРУЗКІ

### GitHub:

1. Адкрыйце `https://github.com/newmathphys/belyzor`
2. Праверце што ўсе файлы на месцы
3. Дадайце апісанне і тэгі

### Hugging Face:

1. Адкрыйце `https://huggingface.co/spaces/newmathphys/belyzor`
2. Праверце што Gradio запускаецца
3. Пратэсцiруйце пошук

---

## 🎯 ШТО ДАЛЕЙ?

### Для GitHub:

- [ ] Дадайце LICENSE
- [ ] Дадайце CONTRIBUTING.md
- [ ] Стварыце Issues template
- [ ] Дадайце GitHub Actions для тэстаў

### Для Hugging Face:

- [ ] Настройце аўта-абнаўленне
- [ ] Дадайце Space metadata
- [ ] Стварыце demo video
- [ ] Дадайце прыклады выкарыстання

---

## 📞 КАРАНТЫСНЫЯ СПАСЫЛКІ

- **GitHub Docs:** https://docs.github.com
- **Hugging Face Docs:** https://huggingface.co/docs
- **Gradio Docs:** https://gradio.app/docs

---

**Гатова да загрузкі!** 🚀🇧🇾
