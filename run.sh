#!/bin/bash

# Дадаем шлях да праекта
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "📌 PYTHONPATH: $PYTHONPATH"
echo ""

case $1 in
    run)
        echo "🚀 Запуск сістэмы..."
        python3 src/core/ultimate_engine_v1.py
        ;;
    gui)
        echo "🖥️ Запуск графічнага інтэрфейсу..."
        python3 src/gui/gui_app.py
        ;;
    web)
        echo "🌐 Запуск вэб-інтэрфейсу..."
        python3 src/web/web_server.py
        ;;
    test)
        echo "🧪 Запуск тэстаў..."
        python3 tests/test_system.py
        ;;
    books)
        echo "📚 Спіс кніг:"
        python3 -c "
from pathlib import Path
path = Path('data/raw/history')
for i, f in enumerate(sorted(path.glob('*.txt')), 1):
    size = f.stat().st_size / 1024 / 1024
    print(f'  {i}. {f.name} ({size:.2f} MB)')
print(f'\n  Усяго: {len(list(path.glob(\"*.txt\")))} кніг')
"
        ;;
    assoc)
        echo "🔗 Стварэнне асацыяцый..."
        python3 src/builders/build_associations_v5.py
        ;;
    dicts)
        echo "📖 Загрузка слоўнікаў..."
        python3 src/core/dictionary_loader.py
        ;;
    llm-on)
        echo "🤙 Уключэнне LLM..."
        python3 -c "
from src.core.llm_interface import LLMInterface
import sys
provider = sys.argv[1] if len(sys.argv) > 1 else 'ollama'
model = sys.argv[2] if len(sys.argv) > 2 else None
llm = LLMInterface()
llm.enable(provider, model)
" "$2" "$3"
        ;;
    llm-off)
        echo "🚫 Адключэнне LLM..."
        python3 -c "
from src.core.llm_interface import LLMInterface
llm = LLMInterface()
llm.disable()
"
        ;;
    llm-status)
        echo "📊 Статус LLM..."
        python3 -c "
from src.core.llm_interface import LLMInterface
llm = LLMInterface()
s = llm.get_status()
print(f'Уключаны: {s[\"enabled\"]}')
print(f'Provider: {s[\"provider\"]}')
print(f'Model: {s[\"model\"]}')
print(f'Endpoint: {s[\"endpoint\"]}')
print(f'Кастомны endpoint: {s[\"custom_endpoint\"]}')
print(f'Выкарыстоўваецца кастомны: {s[\"use_custom_endpoint\"]}')
print(f'Max tokens: {s[\"max_tokens\"]}')
print(f'Temperature: {s[\"temperature\"]}')
"
        ;;
    llm-test)
        echo "🧪 Тэставанне LLM..."
        python3 src/core/llm_interface.py
        ;;
    llm-custom)
        echo "🔧 Налада кастомнага endpoint..."
        python3 -c "
from src.core.llm_interface import LLMInterface
import sys
llm = LLMInterface()
if len(sys.argv) > 1:
    url = sys.argv[1]
    llm.enable_custom_endpoint(url)
    print(f'✅ Кастомны endpoint уключаны: {url}')
else:
    print('Выкарыстанне: ./run.sh llm-custom <url>')
    print('Прыклад: ./run.sh llm-custom http://192.168.0.116:1234/v1')
" "$2"
        ;;
    llm-enable-custom)
        echo "✅ Уключэнне кастомнага endpoint..."
        python3 -c "
from src.core.llm_interface import LLMInterface
llm = LLMInterface()
llm.enable_custom_endpoint()
"
        ;;
    llm-disable-custom)
        echo "✅ Адключэнне кастомнага endpoint..."
        python3 -c "
from src.core.llm_interface import LLMInterface
llm = LLMInterface()
llm.disable_custom_endpoint()
"
        ;;
    llm-set-url)
        echo "🔧 Устаноўка URL кастомнага endpoint..."
        python3 -c "
from src.core.llm_interface import LLMInterface
import sys
if len(sys.argv) > 1:
    url = sys.argv[1]
    llm = LLMInterface()
    llm.set_custom_endpoint(url)
else:
    print('Выкарыстанне: ./run.sh llm-set-url <url>')
" "$2"
        ;;
    books-list)
        echo "📚 Спіс кніг:"
        python3 -c "
from src.core.book_manager import BookManager
mgr = BookManager()
stats = mgr.get_statistics()
print(f\"Кніг: {stats['books_count']}\")
print(f\"Памер: {stats['total_size_mb']:.2f} MB\")
print(f\"Фактаў: {stats['facts_count']:,}\")
print()
for book in stats['books']:
    print(f\"  📖 {book['name']} ({book['size_mb']:.2f} MB)\")
"
        ;;
    books-add)
        echo "📚 Дадаванне кнігі..."
        python3 -c "
from src.core.book_manager import BookManager
from src.core.ultimate_engine_v1 import BelarusUltimateEngine
import sys
if len(sys.argv) > 1:
    book_path = sys.argv[1]
    mgr = BookManager()
    engine = BelarusUltimateEngine()
    
    with open(book_path, 'r', encoding='utf-8') as f:
        book_text = f.read()
    
    book_name = book_path.split('/')[-1].replace('.txt', '')
    count = engine.add_book(book_text, book_name, 'sentences')
    print(f'✅ Дададзена {count} фактаў з кнігі \"{book_name}\"')
else:
    print('Выкарыстанне: ./run.sh books-add <шлях_да_кнігі.txt>')
" "$2"
        ;;
    books-reindex)
        echo "🔄 Пераіндэксацыя..."
        python3 -c "
from src.core.ultimate_engine_v1 import BelarusUltimateEngine
engine = BelarusUltimateEngine()
engine.reindex_all()
print('✅ Пераіндэксацыя завершана')
"
        ;;
    *)
        echo "Выкарыстанне: ./run.sh [run|gui|web|test|books-*|assoc|dicts|llm-*]"
        echo ""
        echo "Асноўныя каманды:"
        echo "  run        - запусціць сістэму (кансоль)"
        echo "  gui        - запусціць графічны інтэрфейс (PyQt5)"
        echo "  web        - запусціць вэб-інтэрфейс (браўзер)"
        echo "  test       - запусціць аўтатэсты"
        echo "  books      - паказаць спіс кніг"
        echo "  assoc      - стварыць асацыяцыі"
        echo "  dicts      - загрузіць слоўнікі"
        echo ""
        echo "Кнігі:"
        echo "  books-list       - спіс кніг"
        echo "  books-add <file> - дадаць кнігу"
        echo "  books-reindex    - пераіндэксацыя"
        echo ""
        echo "LLM каманды:"
        echo "  llm-on <provider> [model]     - уключыць LLM (ollama|lmstudio|openrouter)"
        echo "  llm-off                       - адключыць LLM"
        echo "  llm-status                    - паказаць статус LLM"
        echo "  llm-test                      - тэставаць LLM"
        echo "  llm-custom <url>              - уключыць кастомны endpoint"
        echo "  llm-enable-custom             - уключыць кастомны endpoint"
        echo "  llm-disable-custom            - адключыць кастомны endpoint"
        echo "  llm-set-url <url>             - усталяваць URL кастомнага endpoint"
        echo ""
        echo "Прыклады:"
        echo "  ./run.sh web                        # Запусціць вэб-сервер"
        echo "  ./run.sh llm-on ollama llama3.2:3b"
        echo "  ./run.sh llm-on lmstudio"
        echo "  ./run.sh llm-custom http://192.168.0.116:1234/v1"
        echo "  ./run.sh books-list"
        echo "  ./run.sh books-add data/raw/history/mybook.txt"
        ;;
esac
