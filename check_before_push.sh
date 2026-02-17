#!/bin/bash

echo "🔍 ПРАВЕРКА ПЕРАД АДПРАЎКАЙ"
echo "=========================="

ERRORS=0

# 1. Тэсты
echo ""
echo "1️⃣ Тэсты..."
./run.sh test > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ Тэсты пройдзены"
else
    echo "  ❌ Тэсты не пройдзены"
    ERRORS=$((ERRORS + 1))
fi

# 2. Сінтаксіс
echo ""
echo "2️⃣ Сінтаксіс..."
python3 -m py_compile src/core/*.py 2>/dev/null
python3 -m py_compile src/web/*.py 2>/dev/null
python3 -m py_compile app.py 2>/dev/null
if [ $? -eq 0 ]; then
    echo "  ✅ Сінтаксіс правільны"
else
    echo "  ❌ Памылкі сінтаксісу"
    ERRORS=$((ERRORS + 1))
fi

# 3. Дакументацыя
echo ""
echo "3️⃣ Дакументацыя..."
for file in README.md LICENSE CONTRIBUTING.md DEPLOYMENT.md; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# 4. Бяспека
echo ""
echo "4️⃣ Бяспека..."
if grep -q "api_key.*=" *.json 2>/dev/null; then
    echo "  ⚠️ Знойдзены api_key у JSON!"
else
    echo "  ✅ Чыста"
fi

# 5. Вялікія файлы
echo ""
echo "5️⃣ Вялікія файлы..."
LARGE_FILES=$(find . -type f -size +10M 2>/dev/null | wc -l)
if [ $LARGE_FILES -gt 0 ]; then
    echo "  ⚠️ Знойдзена файлаў >10MB: $LARGE_FILES"
else
    echo "  ✅ Няма"
fi

echo ""
echo "=========================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ УСЕ ПРАВЕРКІ ПРОЙДЗЕНЫ!"
    exit 0
else
    echo "❌ Знойдзена памылак: $ERRORS"
    exit 1
fi
