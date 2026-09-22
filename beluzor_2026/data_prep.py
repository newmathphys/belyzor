"""
БелУзор v2026: Пайплайн падрыхтоўкі датасэтаў для навучання (SFT/QLoRA)
Аб'ядноўвае: OpenOrca_be (інструкцыі), Wiki (кантэкст), Слоўнікі (лексіка).
Выхад: JSONL файл для трэніроўкі HuggingFace Transformers.
"""

import os
import json
import random
from datasets import load_dataset
from tqdm import tqdm

# Канфігурацыя
OUTPUT_DIR = "data/training"
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "beluzor_instruct_v1.jsonl")

# Шаблон сістэмнага промпта для гістарычнага асістэнта
SYSTEM_PROMPT = (
    "Ты — 'БелУзор', інтэлектуальны асістэнт па гісторыі і культуры Беларусі. "
    "Твае адказы павінны быць дакладнымі, заснаванымі толькі на правераных фактах. "
    "Выкарыстоўвай літаратурную беларускую мову. Калі ты не ведаеш адказу, скажы пра гэта."
)

def load_openorca_be():
    """Загрузка датасэту інструкцый WiNE-iNEFF/1M-OpenOrca_be"""
    print("📥 Загрузка OpenOrca_be...")
    try:
        # У рэальнасці спатрэбіцца аўтарызацыя HF_TOKEN, тут імітуем структуру
        # dataset = load_dataset("WiNE-iNEFF/1M-OpenOrca_be", split="train")
        # Для дэма вяртаем прыклады структуры
        return [
            {"instruction": "Растлумач паняцце 'Вялікае Княства Літоўскае'.", "input": "", "output": "Вялікае Княства Літоўскае — сярэднявечная еўрапейская дзяржава, якая існавала з XIII стагоддзя да 1795 года. Яе асновай сталі землі сучаснай Беларусі і Літвы."},
            {"instruction": "Хто напісаў 'Новую зямлю'?", "input": "", "output": "Аўтарам паэмы 'Новая зямля' з'яўляецца класік беларускай літаратуры Якуб Колас."},
            {"instruction": "Перавядзі на беларускую: 'History of Belarus'.", "input": "", "output": "Гісторыя Беларусі."}
        ]
    except Exception as e:
        print(f"⚠️ Памылка загрузкі OpenOrca: {e}")
        return []

def load_wiki_samples():
    """Сэмплеры з Вікіпедыі для кантэксту"""
    print("📥 Загрузка узораў з Вікіпедыі...")
    return [
        {"instruction": "Раскажы пра Статут ВКЛ 1588 года.", "input": "", "output": "Статут ВКЛ 1588 года — помнік права феадалізму, адзін з найбольш дасканалых кодэксаў таго часу ў Еўропе. Ён быў выдадзены на старабеларускай мове і замацоўваў суверэнітэт Вялікага Княства."},
        {"instruction": "Якое значэнне мала Бітва пад Грунвальдам?", "input": "", "output": "Бітва пад Грунвальдам (1410) стала пераломным момантам у вайне з Тэўтонскім ордэнам. Войскі ВКЛ і Польшчы атрымалі буйную перамогу, што спыніла экспансію крыжакоў на ўсход."}
    ]

def load_dictionary_data():
    """Імітацыя апрацоўкі слоўнікавых артыкулаў для пашырэння лексікі"""
    print("📥 Апрацоўка слоўнікавых даных...")
    # Імітацыя пар "Слова - Вызначэнне" -> "Інструкцыя - Адказ"
    return [
        {"instruction": "Што такое 'Лематызацыя'?", "input": "", "output": "Лематызацыя — гэта прывядзенне словаформы да яе нармальнай формы (лемы). Напрыклад, 'бяжыць' -> 'бегчы'."},
        {"instruction": "Як правільна пісацца слова 'Ўзровень'?", "input": "", "output": "Слова пішацца з унескам 'Ў' (у нескладовае) пасля галосных. Правільна: 'узровень' ці 'ўзровень' у залежнасці ад кантэксту, але як асобнае слова часта выкарыстоўваецца 'ўзровень'."},
        {"instruction": "Тлумачэнне слова 'Талерантнасць'.", "input": "", "output": "Цярпімасць да чужых поглядаў, вераванняў і паводзін. У гісторыі ВКЛ талерантнасць была асновай мірнага суіснавання розных канфесій."}
    ]

def generate_training_jsonl():
    """Генерацыя фінальнага файла для трэніроўкі"""
    all_data = []
    
    # Збор даных
    openorca = load_openorca_be()
    wiki = load_wiki_samples()
    dictionary = load_dictionary_data()
    
    all_data.extend(openorca)
    all_data.extend(wiki)
    all_data.extend(dictionary)
    
    print(f"\n📊 Усяго сабрана запісаў: {len(all_data)}")
    
    # Фарматаванне ў стандарт ChatML / Alpaca для трэніроўкі
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in tqdm(all_data, desc="Фарматаванне JSONL"):
            record = {
                "system": SYSTEM_PROMPT,
                "instruction": item["instruction"],
                "input": item.get("input", ""),
                "output": item["output"]
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print(f"\n✅ Датасэт захаваны ў: {OUTPUT_FILE}")
    print(f"📁 Памер файла: {os.path.getsize(OUTPUT_FILE) / 1024:.2f} KB")
    return OUTPUT_FILE

if __name__ == "__main__":
    generate_training_jsonl()
