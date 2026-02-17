#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 БелУзор v0.1 для Hugging Face Spaces

Запуск:
  python3 app.py
  
Адкрыць:
  http://localhost:7860
"""

import gradio as gr
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.ultimate_engine_v1 import BelarusUltimateEngine
from src.core.llm_interface import LLMInterface

# Ініцыялізацыя
print("🔄 Ініцыялізацыя сістэмы...")
engine = BelarusUltimateEngine()
llm = LLMInterface()

conversation_history = []


def update_llm_settings(provider, model, custom_url, enable_llm):
    """Абнаўленне налад LLM"""
    try:
        if not enable_llm:
            llm.disable()
            return "✅ LLM адключаны"
        
        if provider == "Custom URL":
            if custom_url:
                llm.enable_custom_endpoint(custom_url)
                return f"✅ Custom endpoint: {custom_url}"
            else:
                return "⚠️ Увядзіце URL"
        else:
            llm.enable(provider.lower(), model)
            return f"✅ LLM: {provider}/{model}"
    except Exception as e:
        return f"❌ Памылка: {e}"


def search_answer(question, provider, model, custom_url, enable_llm):
    """Пошук адказу з наладамі LLM"""
    global conversation_history
    
    if not question.strip():
        return "❌ Увядзіце пытанне!"
    
    # Абнаўленне налад LLM
    if enable_llm:
        if provider == "Custom URL":
            if custom_url:
                llm.enable_custom_endpoint(custom_url)
        else:
            llm.enable(provider.lower(), model)
    
    # Пошук фактаў
    facts = engine.answer(question, use_llm_ranking=enable_llm)
    
    if not facts:
        return "❌ На жаль, нічога не знойдзена."
    
    # Калі LLM уключаны
    if enable_llm and llm.enabled:
        try:
            # Даданне кантэксту
            context = []
            if conversation_history:
                context = [f"{msg['role']}: {msg['content']}" 
                          for msg in conversation_history[-6:]]
            
            # Фарміраванне prompt
            if context:
                full_prompt = f"""Гісторыя размовы:
{chr(10).join(context)}

❓ Апошняе пытанне: {question}

📚 ФАКТЫ З БАЗЫ ВЕДАЎ:
{chr(10).join(f'{i+1}. {fact}' for i, fact in enumerate(facts))}

📝 Дай поўны разгорнуты адказ (3-5 сказаў мінімум) з улікам папярэдняй размовы."""
            else:
                full_prompt = llm._create_rag_prompt(question, facts)
            
            llm_answer = llm.generate(full_prompt, context=None)
            
            # Фарматаванне адказу
            response = f"🤖 **Адказ LLM:**\n\n{llm_answer}\n\n"
            response += "**📚 Крыніцы:**\n"
            for i, fact in enumerate(facts[:5], 1):
                response += f"{i}. {fact}\n"
            
            # Захаванне ў гісторыю
            conversation_history.append({
                'role': 'user',
                'content': question
            })
            conversation_history.append({
                'role': 'assistant',
                'content': llm_answer
            })
            
            # Абмежаванне гісторыі
            if len(conversation_history) > 20:
                conversation_history.pop(0)
            
            return response
            
        except Exception as e:
            return f"⚠️ Памылка LLM: {e}\n\n📚 Адказ з базы:\n" + "\n".join(facts[:5])
    
    # Без LLM
    response = "**📚 Знойдзена фактаў:** " + str(len(facts)) + "\n\n"
    for i, fact in enumerate(facts[:10], 1):
        response += f"{i}. {fact}\n"
    
    return response


def clear_history():
    """Ачыстка гісторыі"""
    global conversation_history
    conversation_history = []
    return "✅ Гісторыя ачышчана"


def upload_book(file, parse_mode):
    """Загрузка кнігі ў базу"""
    if file is None:
        return "❌ Абярыце файл!"
    
    try:
        # Чытанне файла
        with open(file.name, 'r', encoding='utf-8') as f:
            book_text = f.read()
        
        book_name = file.name.split('/')[-1].replace('.txt', '')
        
        # Дадаванне кнігі
        facts_count = engine.add_book(book_text, book_name, parse_mode.lower())
        
        return f"✅ Кніга '{book_name}' дададзена!\n📊 Створана фактаў: {facts_count}"
    except Exception as e:
        return f"❌ Памылка: {e}"


def get_llm_status():
    """Атрыманне статусу LLM"""
    status = llm.get_status()
    if status['enabled']:
        return f"✅ {status['provider']}/{status['model']}"
    else:
        return "❌ Адключаны"


# Інтэрфейс Gradio
with gr.Blocks(
    title="БелУзор v0.1",
    css="""
    .gradio-container {
        max-width: 1400px !important;
    }
    #banner {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    #banner h1 {
        font-size: 2.5em;
        margin: 0;
    }
    #banner p {
        font-size: 1.2em;
        opacity: 0.9;
    }
    """
) as demo:
    
    # Банэр
    gr.HTML("""
    <div id="banner">
        <h1>🤖 БелУзор v0.1</h1>
        <p>Інтэлектуальная пошукавая сістэма па гісторыі Беларусі</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            # Налады LLM
            with gr.Accordion("⚙️ Налады LLM", open=False):
                gr.Markdown("**Абярыце LLM provider для разгорнутых адказаў**")
                
                provider_dropdown = gr.Dropdown(
                    choices=[
                        "Ollama",
                        "LM Studio",
                        "OpenRouter",
                        "Custom URL"
                    ],
                    value="Ollama",
                    label="Provider"
                )
                
                model_input = gr.Textbox(
                    label="Мадэль",
                    placeholder="llama3.2:3b",
                    value="llama3.2:3b"
                )
                
                custom_url_input = gr.Textbox(
                    label="Custom URL",
                    placeholder="http://192.168.0.116:1234/v1",
                    visible=False
                )
                
                enable_llm_check = gr.Checkbox(
                    label="🤖 Выкарыстоўваць LLM",
                    value=False,
                    info="Для разгорнутых адказаў з кантэкстам"
                )
                
                llm_status_text = gr.Textbox(
                    label="Статус LLM",
                    value="❌ Адключаны",
                    interactive=False
                )
                
                # Кнопка прымянення налад
                apply_llm_btn = gr.Button("✅ Ужыць налады LLM", variant="secondary")
            
            # Поле пытання
            question_input = gr.Textbox(
                label="Пытанне",
                placeholder="Увядзіце ваша пытанне па гісторыі Беларусі...",
                lines=3,
                scale=2
            )
            
            submit_btn = gr.Button("🔍 Пошук", variant="primary", scale=1)
            
            # Адказ
            output = gr.Textbox(
                label="Адказ",
                lines=10,
                max_lines=20
            )
            
            # Кнопкі
            with gr.Row():
                clear_btn = gr.Button("🗑️ Ачысціць гісторыю", variant="secondary")
                status_btn = gr.Button("📊 Статус LLM", variant="secondary")
        
        with gr.Column(scale=1):
            gr.Markdown("""
            ### 📝 Прыклады пытанняў:
            - Год заснавання Мінска?
            - Хто такі Кастусь Каліноўскі?
            - Што такое Статут 1588 года?
            - Грунвальдская бітва 1410 года
            - Люблінская унія 1569 года
            
            ### 📊 Статыстыка:
            - **Фактаў:** 100,484
            - **Слоў:** 347,517
            - **Кніг:** 19
            - **Слоўнікаў:** 26 🅱️ Бэта
            
            ### ⚙️ Асаблівасці:
            - ✅ Кэш лематызацыі (10x хутчэй)
            - ✅ Кэш API (100x хутчэй)
            - ✅ Кантэкст дыялогу
            - ✅ Пошук крыніц у Google
            """)
            
            # Загрузка кніг
            with gr.Accordion("📚 Дадаць кнігу", open=False):
                gr.Markdown("**Загрузіце кнігу ў базу ведаў**")
                
                book_file = gr.File(
                    label="Абярыце файл (.txt)",
                    file_types=[".txt"],
                    type="filepath"
                )
                
                parse_mode_radio = gr.Radio(
                    choices=["Па сэнтенцыях", "Па раздзелах"],
                    value="Па сэнтенцыях",
                    label="Рэжым парсінгу"
                )
                
                upload_btn = gr.Button("📚 Загрузіць кнігу", variant="primary")
                upload_output = gr.Textbox(
                    label="Вынік",
                    lines=3,
                    max_lines=5
                )
            
            # Статус LLM
            llm_info = gr.Markdown("**LLM:** ❌ Адключаны")
    
    # Апрацоўчыкі
    submit_btn.click(
        fn=search_answer,
        inputs=[
            question_input,
            provider_dropdown,
            model_input,
            custom_url_input,
            enable_llm_check
        ],
        outputs=output
    )
    
    clear_btn.click(
        fn=clear_history,
        outputs=output
    )
    
    # Загрузка кнігі
    upload_btn.click(
        fn=upload_book,
        inputs=[book_file, parse_mode_radio],
        outputs=upload_output
    )
    
    # Абнаўленне налад LLM
    apply_llm_btn.click(
        fn=update_llm_settings,
        inputs=[
            provider_dropdown,
            model_input,
            custom_url_input,
            enable_llm_check
        ],
        outputs=llm_status_text
    )
    
    # Паказ/утоенне Custom URL
    def toggle_custom_url(provider):
        return gr.update(visible=(provider == "Custom URL"))
    
    provider_dropdown.change(
        fn=toggle_custom_url,
        inputs=provider_dropdown,
        outputs=custom_url_input
    )
    
    # Статус LLM
    status_btn.click(
        fn=get_llm_status,
        outputs=llm_info
    )
    
    # Гарачыя клавішы
    question_input.submit(
        fn=search_answer,
        inputs=[
            question_input,
            provider_dropdown,
            model_input,
            custom_url_input,
            enable_llm_check
        ],
        outputs=output
    )


if __name__ == "__main__":
    print("✅ Сістэма гатова!")
    print("🌐 Адкрыйце: http://localhost:7860")
    print("⚙️ Налады LLM даступныя ў акне '⚙️ Налады LLM'")
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
