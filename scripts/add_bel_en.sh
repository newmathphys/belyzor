#!/bin/bash

# Скрыпт для дадавання энцыклапедый bel-en у базу

echo "📚 Даданне беларускай энцыклапедыі (bel-en) у базу..."
echo ""

cd /home/mrbritneyxxx/belarus-etalon-2

# Лічильнік
total_facts=0
total_books=0

# Функцыя для дадавання кнігі
add_book() {
    local file=$1
    local book_name=$(basename "$file" .txt)
    
    echo "📖 Апрацоўка: $book_name"
    
    python3 -c "
from src.core.ultimate_engine_v1 import BelarusUltimateEngine
import sys

engine = BelarusUltimateEngine()

with open('$file', 'r', encoding='utf-8') as f:
    book_text = f.read()

count = engine.add_book(book_text, '$book_name', 'sentences')
print(f'   ✅ Дададзена {count} фактаў')
" 2>&1 | grep "Дададзена"
    
    total_facts=$((total_facts + count))
    total_books=$((total_books + 1))
}

# Дадаванне ўсіх тамоў энцыклапедыі
for file in data/raw/bel-en/encyclopedia_volume_*.txt; do
    if [ -f "$file" ]; then
        add_book "$file"
        echo ""
    fi
done

echo "================================"
echo "✅ Завяршэнне!"
echo "   Дададзена кніг: $total_books"
echo "   Усяго фактаў: $total_facts"
echo ""
echo "🔄 Цяпер трэба перазапусціць вэб-сервер:"
echo "   ./run.sh web"
