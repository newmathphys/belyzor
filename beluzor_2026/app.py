# -*- coding: utf-8 -*-
"""
БелУзор v2026: Дэманстрацыйны дадатак для Hugging Face Spaces
Аўтар: BelUzor Team
Тэхналогіі: Gradio, NetworkX, Plotly, Pandas
Запуск: python app.py (лакальна) або размясціць у HF Spaces з requirements.txt
"""

import gradio as gr
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from datetime import datetime
import random
import re

# ==========================================
# 1. ІМІТАЦЫЯ BACKEND (Mocking Advanced Architecture)
# ==========================================

class MockHybridSearchEngine:
    """Імітуе гібрыдны пошук (BM25 + Dense Vector + RRF)"""
    
    def __init__(self):
        # База ведаў (скарочаная для дэма)
        self.knowledge_base = [
            {
                "id": 1,
                "text": "Францыск Скарына нарадзіўся каля 1490 года ў Полацку. Ён заснаваў беларускае кнігадрукаванне.",
                "source": "Энцыклапедыя гісторыі Беларусі, Том 6",
                "year": 1490,
                "entities": ["Францыск Скарына", "Полацк"],
                "score_bm25": 0.85,
                "score_dense": 0.92
            },
            {
                "id": 2,
                "text": "Бітва пад Грунвальдам адбылася 15 ліпеня 1410 года. Войскі ВКЛ і Польшчы разбілі Тэўтонскі ордэн.",
                "source": "Падручнік гісторыі Беларусі, 6 клас",
                "year": 1410,
                "entities": ["Бітва пад Грунвальдам", "ВКЛ", "Польшча", "Тэўтонскі ордэн"],
                "score_bm25": 0.78,
                "score_dense": 0.88
            },
            {
                "id": 3,
                "text": "Статут ВКЛ 1588 года, распрацаваны Львом Сапегам, стаў вяршыняй прававой думкі Еўропы таго часу.",
                "source": "Гісторыя права Беларусі",
                "year": 1588,
                "entities": ["Статут ВКЛ", "Леў Сапега"],
                "score_bm25": 0.65,
                "score_dense": 0.95
            },
            {
                "id": 4,
                "text": "У 1918 годзе была абвешчана Беларуская Народная Рэспубліка (БНР). Першы ўрад узначаліў Ян Серада.",
                "source": "Навуковыя працы Інстытута гісторыі НАН",
                "year": 1918,
                "entities": ["БНР", "Ян Серада"],
                "score_bm25": 0.70,
                "score_dense": 0.82
            }
        ]

    def search(self, query, top_k=5):
        """Сімулюе пошук і вяртае вынікі з RRF (Reciprocal Rank Fusion)"""
        # У рэальнасці тут быў бы запыт да Qdrant/FAISS і Elasticsearch
        results = sorted(self.knowledge_base, key=lambda x: x['score_dense'], reverse=True)[:top_k]
        
        # Разлік RRF Score (імітацыя)
        for i, res in enumerate(results):
            res['rrf_score'] = 1 / (60 + i) 
            res['rank'] = i + 1
            
        return results

class MockReranker:
    """Імітуе BGE-Reranker-v2-m3 для фільтрацыі кантэксту"""
    def rerank(self, query, candidates):
        # Сімуляцыя змены парадку пасля глыбокага аналізу сэнсу
        if "Скарына" in query or "кніга" in query:
            # Паднімаем Скарыну ўверх
            candidates.sort(key=lambda x: 1 if "Скарына" in x['text'] else 0, reverse=True)
        return candidates[:3] # Вяртаем толькі топ-3 для LLM

class MockGraphRAG:
    """Імітуе пабудову графа ведаў і пошук сувязей"""
    def get_graph_data(self, query):
        G = nx.Graph()
        
        # Дынамічная пабудова графа ў залежнасці ад запыту
        if "Скарына" in query:
            nodes = [("Францыск Скарына", "Асоба"), ("Полацк", "Горад"), ("Празірская друкарня", "Месца"), ("Біблія", "Кніга")]
            edges = [("Францыск Скарына", "Полацк", "Нарадзіўся ў"), 
                     ("Францыск Скарына", "Празірская друкарня", "Заснаваў"),
                     ("Францыск Скарына", "Біблія", "Выдаў")]
        elif "Грунвальд" in query:
            nodes = ["Вітаўт", "Ягайла", "Тэўтонскі ордэн", "Грунвальд"]
            edges = [("Вітаўт", "Ягайла", "Саюзнікі"), ("Вітаўт", "Тэўтонскі ордэн", "Вораг"), ("Ягайла", "Грунвальд", "Бітва")]
        else:
            nodes = ["Беларусь", "Мінск", "Полацк", "ВКЛ"]
            edges = [("Мінск", "Беларусь", "Сталіца"), ("Полацк", "ВКЛ", "Частка")]

        G.add_nodes_from(nodes)
        G.add_edges_from(edges)
        
        return G

class MockNLPProcessor:
    """Імітуе Stanza/SpaCy для NER і аналізу правапісу"""
    def analyze(self, text):
        entities = []
        # Простая эврыстыка для дэма
        if "Скарына" in text: entities.append(("Францыск Скарына", "PERSON"))
        if "Полацк" in text: entities.append(("Полацк", "LOCATION"))
        if "1490" in text: entities.append(("1490", "DATE"))
        if "Сапега" in text: entities.append(("Леў Сапега", "PERSON"))
        if "1588" in text: entities.append(("1588", "DATE"))
        
        orthography = "Наркамівка" if "ў" in text or "і" in text else "Тарашкевіца (магчыма)"
        return entities, orthography

# Ініцыялізацыя кампанентаў
search_engine = MockHybridSearchEngine()
reranker = MockReranker()
graph_rag = MockGraphRAG()
nlp_processor = MockNLPProcessor()

# ==========================================
# 2. ЛОГІКА RAG PIPELINE
# ==========================================

def generate_response(message, history):
    """Асноўная функцыя апрацоўкі запыту карыстальніка"""
    if not message:
        return "", [], None, ""

    # Крок 1: Пошук (Hybrid Search)
    raw_results = search_engine.search(message, top_k=5)
    
    # Крок 2: Рэранжыраванне (Reranking)
    refined_results = reranker.rerank(message, raw_results)
    
    # Крок 3: Фарміраванне кантэксту
    context_text = "\n".join([f"[{r['source']}] {r['text']}" for r in refined_results])
    
    # Крок 4: Генерацыя адказу (Імітацыя Llama 3.2 / GPT-4o)
    # У рэальнасці тут быў бы запыт да API
    if "Скарына" in message:
        answer = "Францыск Скарына — першадрукар, асветнік і пісьменнік. Ён нарадзіўся ў Полацку каля 1490 года і выдаў першую друкаваную Біблію на ўсходнеславянскіх землях."
    elif "Грунвальд" in message:
        answer = "Бітва пад Грунвальдам (1410) стала адной з найбуйнейшых у Сярэднявеччы. Аб'яднаныя войскі ВКЛ і Польшчы спынілі экспансію Тэўтонскага ордэна."
    elif "Статут" in message:
        answer = "Статут ВКЛ 1588 года пад кіраўніцтвам Льва Сапегі замацаваў суверэнітэт Вялікага Княства і стаў узорам еўрапейскага права."
    else:
        answer = "Згодна з даступнымі крыніцамі, я знайшоў наступную інфармацыю па вашым запыце. Гісторыя Беларусі багатая на падзеі, і для дакладнага адказу рэкамендуецца звярнуцца да поўных тэкстаў энцыклапедый."

    # Крок 5: Аналіз графа (GraphRAG)
    graph_fig = create_graph_visualization(message)
    
    # Крок 6: NLP Аналіз
    entities, ortho = nlp_processor.analyze(context_text + " " + message)
    nlp_info = f"**Выяўленыя сутнасці:** {', '.join([f'{e[0]} ({e[1]})' for e in entities]) if entities else 'Няма'}\n**Правапіс:** {ortho}"

    # Фарміраванне спісу крыніц для UI
    sources_list = []
    for r in refined_results:
        sources_list.append({
            "Крыніца": r['source'],
            "Тэкст": r['text'][:100] + "...",
            "Рэлевантнасць (RRF)": round(r['rrf_score'], 4)
        })
    
    df_sources = pd.DataFrame(sources_list)
    
    return answer, df_sources, graph_fig, nlp_info

def create_graph_visualization(query):
    """Стварае інтэрактыўны граф Plotly"""
    G = graph_rag.get_graph_data(query)
    
    pos = nx.spring_layout(G, seed=42)
    
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="bottom center",
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=20,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2)
    )
    
    # Каляровая дыферэнцыяцыя
    node_adjacencies = []
    for node in G.nodes():
        node_adjacencies.append(len(list(G.neighbors(node))))
    node_trace.marker.color = node_adjacencies

    fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title=f'Граф ведаў (GraphRAG): {query}',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    return fig

# ==========================================
# 3. ІНТЭРФЕЙС GRADIO
# ==========================================

with gr.Blocks(title="БелУзор v2026") as demo:
    gr.Markdown("""
    # 🇧🇾 БелУзор v2026: Інтэлектуальная сістэма па гісторыі Беларусі
    *Дэманстрацыя перадавых тэхналогій: Hybrid Search (RRF), GraphRAG, NLP (Stanza), Reranking (BGE-M3)*
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Гісторыя дыялогу", height=400)
            msg = gr.Textbox(placeholder="Задайце пытанне па гісторыі Беларусі (напрыклад: 'Хто такі Скарына?' або 'Што такое Статут 1588 года?')", label="Ваш запыт", container=False)
            
            with gr.Row():
                submit_btn = gr.Button("🔍 Знайсці і адказаць", variant="primary")
                clear_btn = gr.Button("🗑️ Ачысціць")
                
        with gr.Column(scale=1):
            gr.Markdown("### 📊 Аналітыка і Крыніцы")
            sources_df = gr.Dataframe(headers=["Крыніца", "Тэкст", "Рэлевантнасць"], label="Знойдзеныя факты (Top-3)")
            nlp_out = gr.Markdown(label="NLP Аналіз")
            
    with gr.Row():
        graph_output = gr.Plot(label="🕸️ Граф ведаў (GraphRAG)")

    def respond(message, chat_history):
        if not message:
            return chat_history, [], None, ""
            
        bot_answer, df_sources, graph_fig, nlp_info = generate_response(message, chat_history)
        
        chat_history.append((message, bot_answer))
        return chat_history, df_sources, graph_fig, nlp_info

    submit_btn.click(respond, [msg, chatbot], [chatbot, sources_df, graph_output, nlp_out])
    clear_btn.click(lambda: ([], [], None, ""), outputs=[chatbot, sources_df, graph_output, nlp_out])
    
    gr.Examples(
        examples=[
            ["Раскажы пра Францыска Скарыну і яго сувязь з Полацкам"],
            ["Якое значэнне мела бітва пад Грунвальдам?"],
            ["Хто такі Леў Сапега і што ён зрабіў у 1588 годзе?"],
            ["Калі была абвешчана БНР?"],
        ],
        inputs=msg
    )

    gr.Markdown("""
    ---
    *Тэхналагічны стэк дэма:* Gradio, NetworkX, Plotly.  
    *Архітэктура:* Імітацыя Hybrid Search (BM25+Dense), Reranker, GraphRAG.  
    *Моўныя мадэлі:* Падтрымка беларускай мовы (Наркамівка/Тарашкевіца).
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
