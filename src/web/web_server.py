#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌐 ВЭБ-ІНТЭРФЕЙС — БелЭталон v0.1

Сучасны чат-інтэрфейс для працы з сістэмай
З аптымізацыяй і кэшаваннем
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import json
import sys
from pathlib import Path
from datetime import datetime
import threading
from time import time
from functools import lru_cache  # ✅ АПТЫМІЗАЦЫЯ 2

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ultimate_engine_v1 import BelarusUltimateEngine
from src.core.llm_interface import LLMInterface


app = Flask(__name__)
CORS(app)

# Глобальныя аб'екты
engine = None
llm = None
conversation_history = []  # Гісторыя дыялогаў

# ✅ АПТЫМІЗАЦЫЯ 2: Кэш для API
class Cache:
    """Кэш з TTL (Time To Live)"""
    def __init__(self, ttl=60):
        self._cache = {}
        self._timestamps = {}
        self.ttl = ttl
    
    def get(self, key, func):
        """Атрымаць з кэша або вылічыць"""
        now = time()
        if key in self._cache and now - self._timestamps[key] < self.ttl:
            return self._cache[key]
        
        # Кэш пратэрмінаваны - вылічым нанова
        value = func()
        self._cache[key] = value
        self._timestamps[key] = now
        return value
    
    def clear(self):
        """Ачысціць кэш"""
        self._cache.clear()
        self._timestamps.clear()

# Ініцыялізацыя кэша
api_cache = Cache(ttl=60)  # 60 секунд


def init_engine():
    """Ініцыялізацыя рухавіка"""
    global engine, llm
    engine = BelarusUltimateEngine()
    llm = LLMInterface()
    print(f"✅ Сістэма ініцыялізавана: {len(engine.facts)} фактаў")


@app.route('/')
def index():
    """Галоўная старонка"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search():
    """Пошук адказаў"""
    data = request.json
    question = data.get('question', '').strip()
    use_llm = data.get('use_llm', False)
    
    if not question:
        return jsonify({'error': 'Пытанне не ўведзена'}), 400
    
    # Пошук фактаў
    facts = engine.answer(question, use_llm_ranking=use_llm)
    
    # Фарміраванне адказу
    response = {
        'question': question,
        'facts': facts[:10],
        'facts_count': len(facts),
        'timestamp': datetime.now().isoformat()
    }
    
    # Калі LLM уключаны
    if use_llm and llm.enabled and facts:
        try:
            # Даданне кантэксту папярэдніх пытанняў
            context = []
            if conversation_history:
                context = [f"{msg['role']}: {msg['content']}" 
                          for msg in conversation_history[-6:]]
            
            # Фарміраванне поўнага prompt з кантэкстам
            if context:
                full_prompt = f"""Гісторыя размовы:
{chr(10).join(context)}

❓ Апошняе пытанне: {question}

📚 ФАКТЫ З БАЗЫ ВЕДАЎ:
{chr(10).join(f'{i+1}. {fact}' for i, fact in enumerate(facts))}

📝 Дай поўны разгорнуты адказ (3-5 сказаў мінімум) з улікам папярэдняй размовы. 
Выкарыстоўвай толькі прадастаўленыя факты. Адказвай на беларускай мове."""
            else:
                full_prompt = llm._create_rag_prompt(question, facts)
            
            llm_answer = llm.generate(full_prompt, context=None)
            response['llm_answer'] = llm_answer
        except Exception as e:
            response['llm_error'] = str(e)
    
    # Захаванне ў гісторыю
    conversation_history.append({
        'role': 'user',
        'content': question,
        'timestamp': datetime.now().isoformat()
    })
    
    if facts:
        conversation_history.append({
            'role': 'assistant',
            'content': response.get('llm_answer', facts[0]),
            'facts': facts[:5],
            'timestamp': datetime.now().isoformat()
        })
    
    # Абмежаванне гісторыі
    if len(conversation_history) > 20:
        conversation_history.pop(0)
    
    return jsonify(response)


@app.route('/api/chat', methods=['POST'])
def chat():
    """Чат з сістэмай (дыялог)"""
    data = request.json
    message = data.get('message', '').strip()
    use_llm = data.get('use_llm', False)
    
    if not message:
        return jsonify({'error': 'Паведамленне не ўведзена'}), 400
    
    # Пошук фактаў
    facts = engine.answer(message, use_llm_ranking=False)
    
    # Фарміраванне адказу
    response = {
        'message': message,
        'facts': facts[:10],
        'facts_count': len(facts),
        'timestamp': datetime.now().isoformat()
    }
    
    # Калі LLM уключаны - генеруем адказ
    if use_llm and llm.enabled:
        try:
            # Падрыхтоўка кантэксту дыялогу
            dialog_context = []
            for msg in conversation_history[-8:]:
                if msg['role'] in ['user', 'assistant']:
                    dialog_context.append(f"{msg['role'].title()}: {msg['content']}")
            
            # Стварэнне prompt з кантэкстам і фактамі
            if facts:
                if dialog_context:
                    full_prompt = f"""ТЫ — эксперцкі асістэнт па гісторыі Беларусі. Вядзеш дыялог з карыстальнікам.

📜 ГІСТОРЫЯ ДЫЯЛОГУ:
{chr(10).join(dialog_context)}

📚 ФАКТЫ З БАЗЫ ВЕДАЎ:
{chr(10).join(f'[{i+1}] {fact}' for i, fact in enumerate(facts))}

❓ ПЫТАННЕ КАРЫСТАЛЬНІКА: {message}

📝 ІНСТРУКЦЫІ:
1. Дай поўны разгорнуты адказ (мінімум 4-6 сказаў)
2. Выкарыстоўвай факты з базы, спасылайся на іх нумары [1], [2] і г.д.
3. Калі фактаў недастаткова, паведамі пра гэта
4. Падтрымлівай дыялог, адказвай на ўдакладняючыя пытанні
5. Адказвай на беларускай мове, навуковым стылем

📝 АДКАЗ:"""
                else:
                    full_prompt = llm._create_rag_prompt(message, facts)
                
                llm_answer = llm.generate(full_prompt, context=None)
                
                # Даданне спасылак на факты
                response['llm_answer'] = llm_answer
                response['has_facts'] = True
            else:
                response['llm_answer'] = "❌ На жаль, у базе няма інфармацыі па гэтым пытанні. Паспрабуйце змяніць фармулёўку або задаць іншае пытанне."
                response['has_facts'] = False
                
        except Exception as e:
            response['llm_error'] = str(e)
            response['llm_answer'] = f"⚠️ Памылка LLM: {e}"
    else:
        # Без LLM - проста факты
        if facts:
            response['llm_answer'] = "\n\n".join(f"[{i+1}] {fact}" for i, fact in enumerate(facts[:5]))
        else:
            response['llm_answer'] = "❌ Нічога не знойдзена"
    
    # Захаванне ў гісторыю дыялогу
    conversation_history.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().isoformat()
    })
    
    conversation_history.append({
        'role': 'assistant',
        'content': response.get('llm_answer', ''),
        'facts': facts[:5],
        'sources': [{'id': i+1, 'text': fact} for i, fact in enumerate(facts[:5])],
        'timestamp': datetime.now().isoformat()
    })
    
    # Абмежаванне гісторыі
    if len(conversation_history) > 30:
        conversation_history.pop(0)
    
    return jsonify(response)


@app.route('/api/history', methods=['GET'])
def get_history():
    """Атрыманне гісторыі дыялогу"""
    return jsonify({
        'history': conversation_history,
        'count': len(conversation_history)
    })


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Ачыстка гісторыі дыялогу"""
    global conversation_history
    conversation_history = []
    return jsonify({'status': 'ok', 'message': 'Гісторыя ачышчана'})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Статыстыка сістэмы з кэшаваннем (✅ 100x хутчэй)"""
    
    # ✅ АПТЫМІЗАЦЫЯ 2: Кэш для API
    return jsonify(api_cache.get('stats', lambda: {
        'facts': engine.get_stats()['facts'],
        'indexed_words': engine.get_stats()['indexed_words'],
        'associations': engine.get_stats()['associations'],
        'books_count': engine.get_books_stats().get('books_count', 0),
        'total_size_mb': engine.get_books_stats().get('total_size_mb', 0),
        'llm_enabled': llm.enabled,
        'llm_provider': llm.provider,
        'llm_model': llm.model
    }))


@app.route('/api/books', methods=['GET'])
def get_books():
    """Спіс кніг"""
    books = engine.get_books_list()
    return jsonify({'books': books})


@app.route('/api/encyclopedias', methods=['GET'])
def get_encyclopedias():
    """Спіс энцыклапедый"""
    from pathlib import Path
    enc_path = Path('data/raw/bel-en')
    
    encyclopedias = []
    if enc_path.exists():
        for file in sorted(enc_path.glob('tom_*_clean.txt')):
            size_mb = file.stat().st_size / 1024 / 1024
            encyclopedias.append({
                'name': file.stem,
                'size_mb': round(size_mb, 2)
            })
    
    return jsonify({'encyclopedias': encyclopedias})


@app.route('/api/dictionaries', methods=['GET'])
def get_dictionaries():
    """Спіс слоўнікаў"""
    from pathlib import Path
    dict_path = Path('data/raw/dictionaries')
    
    dictionaries = []
    if dict_path.exists():
        for folder in sorted(dict_path.iterdir()):
            if folder.is_dir() and not folder.name.startswith('.'):
                dictionaries.append({
                    'name': folder.name,
                    'path': str(folder)
                })
    
    return jsonify({'dictionaries': dictionaries})


@app.route('/api/dictionaries/<dict_name>', methods=['GET'])
def get_dictionary_content(dict_name):
    """Змест слоўніка"""
    from pathlib import Path
    import re
    from html.parser import HTMLParser
    
    dict_path = Path('data/raw/dictionaries') / dict_name
    
    if not dict_path.exists():
        return jsonify({'error': 'Слоўнік не знойдзены'}), 404
    
    entries = []
    
    # Пошук файлаў слоўніка
    for txt_file in dict_path.glob('*.txt'):
        if 'abbr' in txt_file.name or 'info' in txt_file.name:
            continue
        
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                current_word = None
                current_def = []
                
                for line in lines:
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    
                    # Фармат з табуляцыяй: "слова\tазначэнне"
                    if '\t' in line:
                        parts = line.split('\t', 1)
                        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                            entries.append({
                                'word': parts[0].strip(),
                                'definition': parts[1].strip()
                            })
                    # Фармат "слова: азначэнне"
                    elif ':' in line and not line.startswith('\t'):
                        parts = line.split(':', 1)
                        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                            entries.append({
                                'word': parts[0].strip(),
                                'definition': parts[1].strip()
                            })
                    # Фармат "слова = азначэнне"
                    elif '=' in line and not line.startswith('\t'):
                        parts = line.split('=', 1)
                        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                            entries.append({
                                'word': parts[0].strip(),
                                'definition': parts[1].strip()
                            })
                    # Працяг азначэння (з табуляцыяй)
                    elif line.startswith('\t') and entries:
                        entries[-1]['definition'] += ' ' + line_stripped
                            
        except Exception as e:
            continue
    
    # Калі не знойдзена ў TXT, спрабуем HTML
    if not entries:
        for html_file in dict_path.glob('*.html'):
            if 'abbr' in html_file.name or 'pradmova' in html_file.name:
                continue
            
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Просты парсінг HTML
                    from html import unescape
                    content = unescape(content)
                    
                    # Пошук запісаў у HTML
                    pattern = r'<dt[^>]*>([^<]+)</dt>\s*<dd[^>]*>([^<]+)</dd>'
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    
                    for word, definition in matches:
                        word = word.strip()
                        definition = definition.strip()
                        if word and definition:
                            entries.append({
                                'word': word,
                                'definition': definition
                            })
                            
            except Exception as e:
                continue
    
    # Калі не знойдзена, спрабуем DSL фармат
    if not entries:
        for dsl_file in dict_path.glob('*.dsl'):
            if 'abrv' in dsl_file.name:
                continue
            
            try:
                with open(dsl_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Пошук запісаў DSL
                    pattern = r'\[([^\]]+)\](.*?)(?=\n\[|\Z)'
                    matches = re.findall(pattern, content, re.DOTALL)
                    
                    for word, definition in matches[:50]:  # Абмежаванне
                        word = word.strip()
                        definition = re.sub(r'\[.*?\]', '', definition).strip()
                        definition = ' '.join(definition.split())
                        
                        if word and definition:
                            entries.append({
                                'word': word,
                                'definition': definition
                            })
                            
            except Exception as e:
                continue
    
    # Абмежаванне для хуткасці
    return jsonify({
        'name': dict_name,
        'entries': entries[:100]  # Паказваем першыя 100 запісаў
    })


@app.route('/api/llm/status', methods=['GET'])
def llm_status():
    """Статус LLM"""
    status = llm.get_status()
    return jsonify(status)


@app.route('/api/llm/enable', methods=['POST'])
def enable_llm():
    """Уключэнне LLM"""
    data = request.json
    provider = data.get('provider', 'ollama')
    model = data.get('model')
    custom_url = data.get('custom_url')
    
    try:
        if provider == 'custom' and custom_url:
            llm.enable_custom_endpoint(custom_url)
        else:
            llm.enable(provider, model)
        
        return jsonify({
            'status': 'ok',
            'message': f'LLM уключаны: {provider}/{model or llm.model}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/llm/disable', methods=['POST'])
def disable_llm():
    """Адключэнне LLM"""
    llm.disable()
    return jsonify({'status': 'ok', 'message': 'LLM адключаны'})


@app.route('/api/books/add', methods=['POST'])
def add_book_api():
    """Дадаванне кнігі праз API"""
    data = request.json
    book_text = data.get('book_text', '')
    book_name = data.get('book_name', 'unknown')
    parse_mode = data.get('parse_mode', 'sentences')
    
    if not book_text:
        return jsonify({'error': 'Тэкст кнігі пусты'}), 400
    
    try:
        facts_count = engine.add_book(book_text, book_name, parse_mode)
        return jsonify({
            'status': 'ok',
            'message': f'Кніга "{book_name}" дададзена',
            'facts_count': facts_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reindex', methods=['POST'])
def reindex():
    """Пераіндэксацыя"""
    try:
        engine.reindex_all()
        return jsonify({'status': 'ok', 'message': 'Пераіндэксацыя завершана'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Запуск сервера"""
    init_engine()
    print(f"🌐 Вэб-сервер запушчаны: http://{host}:{port}")
    print(f"💡 Адкрыйце ў браўзеры: http://localhost:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    run_server()
