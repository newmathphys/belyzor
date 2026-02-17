# 🤝 Як унесці ўклад у БелУзор

Дзякуй за цікавасць да праекта! Вось як вы можаце дапамагчы.

## 🐛 Паведаміць пра памылку

1. Адкрыйце [Issue](https://github.com/newmathphys/belyzor/issues)
2. Апішыце праблему дэталёва
3. Дадайце крокі для аднаўлення
4. Дадайце версію Python і бібліятэк
5. Прымацуецце скрыншоты (калі ёсць)

## 💡 Прапанаванне функцый

1. Стварыце [Feature Request Issue](https://github.com/newmathphys/belyzor/issues)
2. Апішыце функцыю
3. Тлумачце навошта яна патрэбна
4. Прывядзіце прыклады выкарыстання

## 🔧 Pull Request

### Падрыхтоўка

```bash
# Форкніце рэпазіторый
git clone https://github.com/newmathphys/belyzor.git
cd belyzor

# Стварыце галіну
git checkout -b feature/AmazingFeature
```

### Змены

1. Зрабіце неабходныя змены
2. Дадайце тэсты (калі магчыма)
3. Абнавіце дакументацыю
4. Запусціце `./run.sh test`

### Адпраўка

```bash
git add .
git commit -m 'Add AmazingFeature

Co-authored-by: Qwen-Coder <qwen-coder@alibabacloud.com>'
git push origin feature/AmazingFeature
```

Адкрыйце Pull Request на GitHub!

## 📝 Стандарты кода

- **Водступы:** 4 прабелы
- **Даканументацыя:** Абавязкова для ўсіх функцый
- **Тэсты:** Для новых функцый
- **Type hints:** Выкарыстоўвайце `typing`

## 🧪 Тэставанне

```bash
# Запуск тэстаў
./run.sh test

# Праверка сінтаксісу
python3 -m py_compile src/core/*.py
python3 -m py_compile src/web/*.py
```

## 📚 Карысныя спасылкі

- [README.md](README.md) - Асноўная дакументацыя
- [DEPLOYMENT.md](DEPLOYMENT.md) - Інструкцыі па разгортванні
- [USAGE.md](USAGE.md) - Як карыстацца

Дзякуй за ўклад! 🇧🇾
