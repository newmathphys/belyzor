#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤙 LLM ІНТЭРФЕЙС — Ollama, LM Studio, OpenRouter, Custom

Падтрымка лакальных і аддаленых LLM для генерацыі адказаў
"""

import json
import requests
from pathlib import Path
from typing import Optional, List, Dict


class LLMInterface:
    """
    Універсальны інтэрфейс для LLM

    Падтрымлівае:
    - Ollama (лакальна)
    - LM Studio (лакальна/сетка)
    - OpenRouter (API)
    - Custom endpoint (любы URL)
    - Адключаны рэжым (без LLM)
    """

    def __init__(self, config_path: str = "llm_config.json"):
        self.config = self._load_config(config_path)
        self.enabled = self.config.get('enabled', False)
        self.provider = self.config.get('provider', 'ollama')
        self.model = self.config.get('model', 'llama3.2:3b')

        # Канфігурацыя падключэння з config
        default_endpoints = {
            'ollama': 'http://localhost:11434',
            'lmstudio': 'http://localhost:1234/v1',
            'openrouter': 'https://openrouter.ai/api/v1',
        }
        
        # Загрузка endpoint'ов з канфігурацыі або выкарыстанне default
        config_endpoints = self.config.get('endpoints', default_endpoints)
        self.endpoints = {**default_endpoints, **config_endpoints}
        
        # Кастомны endpoint (прыярытэт)
        self.custom_endpoint = self.config.get('custom_endpoint', '')
        self.use_custom_endpoint = self.config.get('use_custom_endpoint', False)

        self.api_key = self.config.get('api_key', '')

    def _load_config(self, config_path: str) -> dict:
        """Загрузка канфігурацыі"""
        config_file = Path(config_path)
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Канфігурацыя па змаўчанні
        return {
            'enabled': False,  # Адключана па змаўчанні
            'provider': 'ollama',
            'model': 'llama3.2:3b',
            'api_key': '',
            'max_tokens': 500,
            'temperature': 0.3,
        }

    def save_config(self, config_path: str = "llm_config.json"):
        """Захаванне канфігурацыі"""
        config_file = Path(config_path)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def enable(self, provider: str = 'ollama', model: str = None):
        """Уключыць LLM"""
        self.enabled = True
        self.provider = provider
        if model:
            self.model = model
        
        self.config['enabled'] = True
        self.config['provider'] = provider
        if model:
            self.config['model'] = model
        
        self.save_config()
        print(f"✅ LLM уключаны: {provider}/{model or self.model}")

    def disable(self):
        """Адключыць LLM"""
        self.enabled = False
        self.config['enabled'] = False
        self.save_config()
        print("✅ LLM адключаны")

    def generate(self, prompt: str, context: List[str] = None) -> str:
        """
        Генерацыя адказу з LLM

        Args:
            prompt: Пытанне карыстальніка
            context: Спіс фактаў з базы (RAG)

        Returns:
            Згенераваны адказ
        """
        if not self.enabled:
            return ""  # LLM адключаны

        # Фарміраванне RAG prompt
        if context:
            rag_prompt = self._create_rag_prompt(prompt, context)
        else:
            rag_prompt = prompt

        try:
            # Калі ўключаны кастомны endpoint
            if self.use_custom_endpoint and self.custom_endpoint:
                return self._generate_custom(rag_prompt)
            elif self.provider == 'ollama':
                return self._generate_ollama(rag_prompt)
            elif self.provider == 'lmstudio':
                return self._generate_lmstudio(rag_prompt)
            elif self.provider == 'openrouter':
                return self._generate_openrouter(rag_prompt)
            elif self.provider == 'custom':
                return self._generate_custom(rag_prompt)
            else:
                return f"❌ Невядомы provider: {self.provider}"

        except Exception as e:
            return f"⚠️ Памылка LLM: {str(e)}\n\n📚 Адказ з базы:\n" + "\n".join(context or [])

    def _create_rag_prompt(self, question: str, facts: List[str]) -> str:
        """Стварэнне RAG prompt для разгорнутага адказу"""
        return f"""Ты — эксперты па гісторыі Беларусі. Твая задача — даць поўны, дакладны і зразумелы адказ.

📚 ФАКТЫ З БАЗЫ ВЕДАЎ:
{chr(10).join(f'{i+1}. {fact}' for i, fact in enumerate(facts))}

❓ ПЫТАННЕ: {question}

📝 ІНСТРУКЦЫІ:
1. Выкарыстоўвай ТОЛЬКІ прадастаўленыя вышэй факты для адказу
2. Дай поўны і разгорнуты адказ (мінімум 3-5 сказаў)
3. Калі фактаў недастаткова для поўнага адказу, паведамі пра гэта
4. Структуруй адказ: спачатку кароткі адказ, потым дэталі
5. Унікай прыдумвання інфармацыі, якой няма ў фактах
6. Адказвай на беларускай мове

📝 АДКАЗ:"""

    def _generate_ollama(self, prompt: str) -> str:
        """Генерацыя праз Ollama"""
        url = f"{self.endpoints['ollama']}/api/generate"
        
        payload = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': self.config.get('temperature', 0.3),
                'num_predict': self.config.get('max_tokens', 500),
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', '❌ Няма адказу')

    def _generate_lmstudio(self, prompt: str) -> str:
        """Генерацыя праз LM Studio (лакальна або сетка)"""
        # Выкарыстанне кастомнага endpoint калі ўключаны
        if self.use_custom_endpoint and self.custom_endpoint:
            base_url = self.custom_endpoint
        else:
            base_url = self.endpoints['lmstudio']
        
        url = f"{base_url}/chat/completions"

        headers = {
            'Content-Type': 'application/json',
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'Ты — эксперты па гісторыі Беларусі. Давай поўныя і разгорнутыя адказы.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': self.config.get('max_tokens', 1000),
            'temperature': self.config.get('temperature', 0.5),
        }

        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content']

    def _generate_openrouter(self, prompt: str) -> str:
        """Генерацыя праз OpenRouter"""
        url = f"{self.endpoints['openrouter']}/chat/completions"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': 'https://github.com/belarus-etalon-2',
            'X-Title': 'Belarus Etalon 2',
        }

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'Ты — эксперты па гісторыі Беларусі. Давай поўныя і разгорнутыя адказы.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': self.config.get('max_tokens', 1000),
            'temperature': self.config.get('temperature', 0.5),
        }

        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content']

    def _generate_custom(self, prompt: str) -> str:
        """Генерацыя праз кастомны endpoint (OpenAI-сумяшчальны API)"""
        if not self.custom_endpoint:
            raise ValueError("❌ Кастомны endpoint не наладжаны")
        
        url = f"{self.custom_endpoint}/chat/completions"

        headers = {
            'Content-Type': 'application/json',
        }
        
        # Калі патрэбны API ключ для кастомнага endpoint
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'Ты — эксперты па гісторыі Беларусі. Давай поўныя і разгорнутыя адказы на беларускай мове.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': self.config.get('max_tokens', 1000),
            'temperature': self.config.get('temperature', 0.5),
        }

        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content']

    def rank_facts(self, question: str, facts: List[str]) -> List[tuple]:
        """
        Рэранжыраванне фактаў з дапамогай LLM

        Returns:
            Спіс (fact, score) адсартаваны па рэлевантнасці
        """
        if not self.enabled or len(facts) < 2:
            # Калі LLM адключаны, вяртаем як ёсць
            return [(fact, 1.0) for fact in facts]

        prompt = f"""Ацані рэлевантнасць кожнага факту для пытання ад 0 да 1.

❓ Пытанне: {question}

📚 Факты:
{chr(10).join(f'{i+1}. {fact}' for i, fact in enumerate(facts))}

Адказ у фармаце JSON:
{{"1": 0.9, "2": 0.7, ...}}"""

        try:
            # Калі ўключаны кастомны endpoint
            if self.use_custom_endpoint and self.custom_endpoint:
                response = self._generate_custom(prompt)
            elif self.provider == 'ollama':
                response = self._generate_ollama(prompt)
            elif self.provider == 'lmstudio':
                response = self._generate_lmstudio(prompt)
            elif self.provider == 'openrouter':
                response = self._generate_openrouter(prompt)
            elif self.provider == 'custom':
                response = self._generate_custom(prompt)
            else:
                return [(fact, 1.0) for fact in facts]

            # Парсінг адказу
            scores = json.loads(response)

            # Стварэнне спісу з ацэнкамі
            ranked = []
            for i, fact in enumerate(facts):
                score = float(scores.get(str(i+1), 0.5))
                ranked.append((fact, score))

            # Сартыроўка па рэлевантнасці
            ranked.sort(key=lambda x: -x[1])
            return ranked

        except Exception as e:
            # Калі памылка, вяртаем як ёсць
            return [(fact, 1.0) for fact in facts]

    def get_status(self) -> Dict:
        """Статус LLM"""
        # Вызначэнне бягучага endpoint
        if self.use_custom_endpoint and self.custom_endpoint:
            current_endpoint = self.custom_endpoint
        else:
            current_endpoint = self.endpoints.get(self.provider, 'unknown')
        
        return {
            'enabled': self.enabled,
            'provider': self.provider,
            'model': self.model,
            'endpoint': current_endpoint,
            'custom_endpoint': self.custom_endpoint,
            'use_custom_endpoint': self.use_custom_endpoint,
            'max_tokens': self.config.get('max_tokens', 1000),
            'temperature': self.config.get('temperature', 0.5),
        }

    def set_custom_endpoint(self, url: str):
        """Устаноўка кастомнага endpoint"""
        self.custom_endpoint = url
        self.config['custom_endpoint'] = url
        self.save_config()
        print(f"✅ Кастомны endpoint: {url}")

    def enable_custom_endpoint(self, url: str = None):
        """Уключэнне кастомнага endpoint"""
        if url:
            self.custom_endpoint = url
            self.config['custom_endpoint'] = url
        self.use_custom_endpoint = True
        self.config['use_custom_endpoint'] = True
        self.enabled = True
        self.config['enabled'] = True
        self.save_config()
        print(f"✅ Кастомны endpoint уключаны: {self.custom_endpoint}")

    def disable_custom_endpoint(self):
        """Адключэнне кастомнага endpoint"""
        self.use_custom_endpoint = False
        self.config['use_custom_endpoint'] = False
        self.save_config()
        print("✅ Кастомны endpoint адключаны")


def main():
    """Тэставанне LLM інтэрфейсу"""
    print("="*80)
    print("🤙 LLM ІНТЭРФЕЙС — ТЭСТАВАННЕ")
    print("="*80)
    
    llm = LLMInterface()
    
    # Статус
    status = llm.get_status()
    print(f"\n📊 Статус:")
    print(f"   Уключаны: {status['enabled']}")
    print(f"   Provider: {status['provider']}")
    print(f"   Model: {status['model']}")
    print(f"   Endpoint: {status['endpoint']}")
    
    # Тэст генерацыі
    print("\n🧪 Тэст генерацыі:")
    
    facts = [
        "Кастусь Каліноўскі нарадзіўся ў 1838 годзе",
        "Ён быў кіраўніком паўстання 1863 года",
        "Выдаваў газету «Мужыцкая праўда»",
    ]
    
    answer = llm.generate(
        prompt="Хто такі Кастусь Каліноўскі?",
        context=facts
    )
    
    if answer:
        print(f"\n📝 Адказ LLM:\n{answer}")
    else:
        print("\n⚠️ LLM адключаны або недаступны")
    
    # Тэст рэранжыравання
    print("\n📊 Тэст рэранжыравання:")
    ranked = llm.rank_facts(
        question="Калі нарадзіўся Каліноўскі?",
        facts=facts
    )
    
    print("Адсартаваныя факты:")
    for i, (fact, score) in enumerate(ranked, 1):
        print(f"  {i}. [{score:.2f}] {fact[:50]}...")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
