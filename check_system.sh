#!/bin/bash

echo "======================================"
echo "🧠🇧🇾 БЕЛУЗОР v0.1 — ПРАВЕРКА СІСТЭМЫ"
echo "======================================"
echo ""

cd /home/mrbritneyxxx/belarus-etalon-2

# 1. Праверка файлаў
echo "1️⃣ Праверка файлаў..."
echo ""

if [ -f "src/web/web_server.py" ]; then
    echo "  ✅ Вэб-сервер"
else
    echo "  ❌ Вэб-сервер не знойдзены"
fi

if [ -f "src/core/ultimate_engine_v1.py" ]; then
    echo "  ✅ Рухавік"
else
    echo "  ❌ Рухавік не знойдзены"
fi

if [ -f "data/etalons/facts.json" ]; then
    echo "  ✅ База фактаў"
else
    echo "  ❌ База фактаў не знойдзена"
fi

echo ""

# 2. Праверка колькасці фактаў
echo "2️⃣ Праверка базы фактаў..."
echo ""

python3 -c "
import json
with open('data/etalons/facts.json', 'r', encoding='utf-8') as f:
    facts = json.load(f)
print(f'  📊 Фактаў: {len(facts):,}')

from collections import Counter
sources = Counter(fact.get('book', 'unknown') for fact in facts)
print(f'  📚 Крыніц: {len(sources)}')
"

echo ""

# 3. Праверка вэб-сервера
echo "3️⃣ Праверка вэб-сервера..."
echo ""

if curl -s http://localhost:5000/api/stats > /dev/null 2>&1; then
    echo "  ✅ Вэб-сервер працуе"
    curl -s http://localhost:5000/api/stats | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'  📊 Фактаў: {data[\"facts\"]:,}')
print(f'  🔍 Слоў: {data[\"indexed_words\"]:,}')
print(f'  📚 Кніг: {data[\"books_count\"]}')
print(f'  🤙 LLM: {\"✅ \" + data[\"llm_provider\"] if data[\"llm_enabled\"] else \"❌ Адключаны\"}')
"
else
    echo "  ⚠️ Вэб-сервер не працуе"
    echo "  💡 Запусціце: ./run.sh web"
fi

echo ""

# 4. Тэст пошуку
echo "4️⃣ Тэст пошуку..."
echo ""

python3 -c "
import sys
sys.path.insert(0, '.')
from src.core.ultimate_engine_v1 import BelarusUltimateEngine

engine = BelarusUltimateEngine()
facts = engine.answer('Хто такі Кастусь Каліноўскі?', use_llm_ranking=False)

print(f'  ❓ Пытанне: Хто такі Кастусь Каліноўскі?')
print(f'  ✅ Знойдзена фактаў: {len(facts)}')
if facts:
    print(f'  📖 Першы факт: {facts[0][:80]}...')
" 2>&1 | grep -E "(❓|✅|📖)"

echo ""

# 5. Вынікі
echo "======================================"
echo "📊 ВЫНІКІ"
echo "======================================"
echo ""

# Агульная колькасць фактаў
TOTAL_FACTS=$(python3 -c "import json; print(len(json.load(open('data/etalons/facts.json'))))")

if [ "$TOTAL_FACTS" -gt "100000" ]; then
    echo "✅ Фактаў: $TOTAL_FACTS (>100K)"
else
    echo "⚠️ Фактаў: $TOTAL_FACTS (менш за 100K)"
fi

# Праверка вэб-сервера
if curl -s http://localhost:5000/api/stats > /dev/null 2>&1; then
    echo "✅ Вэб-сервер: працуе"
else
    echo "⚠️ Вэб-сервер: не працуе"
fi

# Праверка LLM
LLM_STATUS=$(curl -s http://localhost:5000/api/llm/status 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('enabled', False))" 2>/dev/null || echo "False")

if [ "$LLM_STATUS" = "True" ]; then
    echo "✅ LLM: уключаны"
else
    echo "⚠️ LLM: адключаны"
fi

echo ""
echo "======================================"
echo "💡 КАМАНДЫ:"
echo "======================================"
echo ""
echo "  ./run.sh web          - запусціць вэб-сервер"
echo "  ./run.sh test         - запусціць тэсты"
echo "  ./run.sh books-list   - спіс кніг"
echo "  ./run.sh llm-status   - статус LLM"
echo ""
echo "  http://localhost:5000 - адкрыць вэб-інтэрфейс"
echo ""
echo "======================================"
