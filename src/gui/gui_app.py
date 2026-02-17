#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🖥️ GUI ІНТЭРФЕЙС ДЛЯ БЕЛЭТАЛОН v0.1

Графічная абалонка з наладамі LLM, пошукам і статыстыкай
"""

import sys
import json
import threading
from pathlib import Path

# Праверка наяўнасці PyQt5
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
        QTabWidget, QGroupBox, QSpinBox, QDoubleSpinBox,
        QCheckBox, QStatusBar, QProgressBar, QMessageBox,
        QFileDialog, QListWidget, QListWidgetItem, QSplitter,
        QFrame, QScrollArea
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt5 не знойдзены. Усталюйце: pip install PyQt5")

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.ultimate_engine_v1 import BelarusUltimateEngine
from src.core.llm_interface import LLMInterface


class SearchWorker(QThread):
    """Worker для пошуку ў асобным патоцы"""
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, engine, llm, question, use_llm, conversation_context=None):
        super().__init__()
        self.engine = engine
        self.llm = llm
        self.question = question
        self.use_llm = use_llm
        self.conversation_context = conversation_context or []

    def run(self):
        try:
            # Калі LLM уключаны і ёсць кантэкст размовы
            if self.use_llm and self.llm.enabled:
                # Пошук фактаў
                facts = self.engine.answer(self.question, use_llm_ranking=False)
                if facts:
                    # Даданне кантэксту размовы
                    context_text = "\n".join(self.conversation_context[-5:])  # Апошнія 5 рэплік
                    full_prompt = f"""Гісторыя размовы:
{context_text}

❓ Апошняе пытанне: {self.question}

📚 ФАКТЫ З БАЗЫ:
{chr(10).join(f'{i+1}. {fact}' for i, fact in enumerate(facts))}

📝 Дай поўны адказ з улікам папярэдняй размовы:"""
                    
                    answer = self.llm.generate(full_prompt, context=None)
                    result = f"""================================================================================
📚 АДКАЗ НА ЗАПЫТ: "{self.question}"
================================================================================

🤙 Адказ LLM:

{answer}

--------------------------------------------------------------------------------
📚 Крыніцы (факты з базы):

✅ Знойдзена фактаў: {len(facts)}
"""
                    for i, fact in enumerate(facts[:5], 1):
                        result += f"\n{i}. 📖 {fact}"
                    
                    result += "\n\n" + "="*80
                    self.result_ready.emit(result)
                else:
                    self.result_ready.emit(f"❌ Нічога не знойдзена па запыце: {self.question}")
            else:
                result = self.engine.answer_formatted(self.question, use_llm=self.use_llm)
                self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class BelEtonGUI(QMainWindow):
    """Галоўнае акно GUI"""

    def __init__(self):
        super().__init__()
        self.engine = None
        self.llm = None
        self.search_worker = None
        self.history = []
        self.conversation_context = []  # Кантэкст размовы

        self.init_ui()
        self.init_engine()
        self.load_settings()

    def init_ui(self):
        """Ініцыялізацыя інтэрфейсу"""
        self.setWindowTitle("🧠 БелЭталон v0.1 — Інтэлектуальны пошук")

        # Цэнтральнае размяшчэнне акна
        screen_geometry = QApplication.desktop().screenGeometry()
        window_width = 1200
        window_height = 800
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        # Прымусовае адлюстраванне
        self.raise_()
        self.activateWindow()

        # Галоўны віджэт
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Верхняя панэль
        self.create_header_panel(main_layout)

        # Раздзяляльнік
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Левая панэль (налады)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        self.create_settings_panel(left_layout)
        splitter.addWidget(left_widget)

        # Правая панэль (пошук і вынікі)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.create_search_panel(right_layout)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # Статусная радок
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Гатова")

        # Прагрэс бар
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.statusBar.addPermanentWidget(self.progress)

    def create_header_panel(self, layout):
        """Стварэнне верхняй панэлі"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)

        # Загаловак
        title = QLabel("🧠 БелЭталон v0.1")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        header_layout.addWidget(title)

        # Індыкатар LLM (зялёны/шэры)
        self.llm_indicator = QFrame()
        self.llm_indicator.setFixedSize(12, 12)
        self.llm_indicator.setStyleSheet("background-color: #95a5a6; border-radius: 6px;")
        self.llm_indicator.setToolTip("LLM адключаны")
        header_layout.addWidget(self.llm_indicator)

        # Статус LLM
        self.llm_status = QLabel("❌ LLM адключаны")
        self.llm_status.setStyleSheet("font-size: 14px; color: #95a5a6;")
        header_layout.addWidget(self.llm_status)

        header_layout.addStretch()

        layout.addWidget(header_frame)

    def create_settings_panel(self, layout):
        """Стварэнне панэлі налад"""
        # LLM налады
        llm_group = QGroupBox("🤙 LLM Налады")
        llm_layout = QVBoxLayout(llm_group)

        # Provider
        llm_layout.addWidget(QLabel("Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(['Адключаны', 'Ollama', 'LM Studio', 'OpenRouter', 'Custom'])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        llm_layout.addWidget(self.provider_combo)

        # Мадэль
        llm_layout.addWidget(QLabel("Мадэль:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            'llama3.2:3b',
            'llama3.2:7b',
            'mistral:7b',
            'gemma2:9b',
            'meta-llama/llama-3-8b-instruct',
            'google/gemma-3-4b',
        ])
        llm_layout.addWidget(self.model_combo)

        # Custom endpoint URL
        llm_layout.addWidget(QLabel("🔗 Custom Endpoint URL:"))
        self.custom_url_input = QLineEdit()
        self.custom_url_input.setPlaceholderText("http://192.168.0.116:1234/v1")
        self.custom_url_input.setToolTip("Прыклад: http://192.168.0.116:1234/v1")
        llm_layout.addWidget(self.custom_url_input)

        # Кнопкі для custom endpoint
        custom_btn_layout = QHBoxLayout()
        self.custom_enable_btn = QPushButton("✅ Уключыць custom")
        self.custom_enable_btn.clicked.connect(self.enable_custom_endpoint)
        custom_btn_layout.addWidget(self.custom_enable_btn)

        self.custom_disable_btn = QPushButton("❌ Адключыць custom")
        self.custom_disable_btn.clicked.connect(self.disable_custom_endpoint)
        custom_btn_layout.addWidget(self.custom_disable_btn)

        llm_layout.addLayout(custom_btn_layout)

        # Тэмпература
        llm_layout.addWidget(QLabel("Тэмпература (0-1):"))
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 1.0)
        self.temperature_spin.setValue(0.5)
        self.temperature_spin.setSingleStep(0.1)
        llm_layout.addWidget(self.temperature_spin)

        # Max tokens
        llm_layout.addWidget(QLabel("Max tokens:"))
        self.tokens_spin = QSpinBox()
        self.tokens_spin.setRange(100, 2000)
        self.tokens_spin.setValue(1000)
        self.tokens_spin.setSingleStep(100)
        llm_layout.addWidget(self.tokens_spin)

        # Кнопкі
        btn_layout = QHBoxLayout()
        self.llm_enable_btn = QPushButton("✅ Уключыць LLM")
        self.llm_enable_btn.clicked.connect(self.enable_llm)
        btn_layout.addWidget(self.llm_enable_btn)

        self.llm_test_btn = QPushButton("🧪 Тэст")
        self.llm_test_btn.clicked.connect(self.test_llm)
        btn_layout.addWidget(self.llm_test_btn)

        llm_layout.addLayout(btn_layout)
        layout.addWidget(llm_group)

        # Кнігі
        books_group = QGroupBox("📚 Кнігі")
        books_layout = QVBoxLayout(books_group)

        # Спіс кніг
        self.books_list = QListWidget()
        self.books_list.setMaximumHeight(150)
        self.books_list.setToolTip("Спіс кніг у базе")
        books_layout.addWidget(self.books_list)

        # Кнопкі для кніг
        books_btn_layout = QHBoxLayout()

        self.add_book_btn = QPushButton("📁 Дадаць кнігу")
        self.add_book_btn.setToolTip("Дадаць новую кнігу ў базу")
        self.add_book_btn.clicked.connect(self.add_book)
        books_btn_layout.addWidget(self.add_book_btn)

        self.reindex_btn = QPushButton("🔄 Пераіндэксаваць")
        self.reindex_btn.setToolTip("Пераіндэксаваць усе кнігі")
        self.reindex_btn.clicked.connect(self.reindex_books)
        books_btn_layout.addWidget(self.reindex_btn)

        books_layout.addLayout(books_btn_layout)

        # Статыстыка кніг
        self.books_stats_label = QLabel("Загрузка...")
        self.books_stats_label.setWordWrap(True)
        books_layout.addWidget(self.books_stats_label)

        layout.addWidget(books_group)

        # Статыстыка
        stats_group = QGroupBox("📊 Статыстыка")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("Загрузка...")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)

        layout.addWidget(stats_group)

        # Гісторыя
        history_group = QGroupBox("📝 Гісторыя")
        history_layout = QVBoxLayout(history_group)

        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.on_history_clicked)
        history_layout.addWidget(self.history_list)

        clear_btn = QPushButton("🗑️ Ачысціць гісторыю")
        clear_btn.clicked.connect(self.clear_history)
        history_layout.addWidget(clear_btn)

        layout.addWidget(history_group)

        layout.addStretch()

    def create_search_panel(self, layout):
        """Стварэнне панэлі пошуку"""
        # Поле пошуку
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("❓ Увядзіце пытанне па гісторыі Беларусі...")
        self.search_input.setFont(QFont("Arial", 12))
        self.search_input.returnPressed.connect(self.search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("🔍 Пошук")
        self.search_btn.setFont(QFont("Arial", 12))
        self.search_btn.clicked.connect(self.search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Опцыі
        options_layout = QHBoxLayout()

        self.use_llm_check = QCheckBox("🤙 Выкарыстоўваць LLM")
        self.use_llm_check.setChecked(False)
        self.use_llm_check.stateChanged.connect(self.on_llm_check_changed)
        options_layout.addWidget(self.use_llm_check)

        self.clear_context_btn = QPushButton("🗑️ Ачысціць кантэкст")
        self.clear_context_btn.setToolTip("Ачысціць гісторыю размовы для новага дыялогу")
        self.clear_context_btn.clicked.connect(self.clear_conversation_context)
        options_layout.addWidget(self.clear_context_btn)

        options_layout.addStretch()
        layout.addLayout(options_layout)

        # Вынікі
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Courier New", 10))
        layout.addWidget(self.results_text)

        # Кнопкі дзеянняў
        btn_layout = QHBoxLayout()

        export_btn = QPushButton("📁 Экспарт")
        export_btn.clicked.connect(self.export_results)
        btn_layout.addWidget(export_btn)

        copy_btn = QPushButton("📋 Капіяваць")
        copy_btn.clicked.connect(self.copy_results)
        btn_layout.addWidget(copy_btn)

        clear_btn = QPushButton("🗑️ Ачысціць")
        clear_btn.clicked.connect(self.clear_results)
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def init_engine(self):
        """Ініцыялізацыя рухавіка"""
        self.statusBar.showMessage("Ініцыялізацыя сістэмы...")

        try:
            self.engine = BelarusUltimateEngine()
            self.llm = LLMInterface()

            # Абнаўленне статыстыкі
            self.update_stats()
            
            # Абнаўленне спісу кніг
            self.update_books_list()

            # Абнаўленне індыкатара LLM
            self.update_llm_indicator()

            self.statusBar.showMessage("Сістэма гатова!")
        except Exception as e:
            QMessageBox.critical(self, "Памылка", f"Не ўдалося ініцыялізаваць сістэму:\n{e}")

    def update_llm_indicator(self):
        """Абнаўленне індыкатара LLM (зялёны/шэры)"""
        if self.llm and self.llm.enabled:
            # Зялёны індыкатар
            self.llm_indicator.setStyleSheet("background-color: #27ae60; border-radius: 6px;")
            self.llm_indicator.setToolTip(f"✅ LLM уключаны: {self.llm.provider} / {self.llm.model}")
            self.llm_status.setText(f"✅ LLM: {self.llm.provider}/{self.llm.model}")
            self.llm_status.setStyleSheet("font-size: 14px; color: #27ae60;")
        else:
            # Шэры індыкатар
            self.llm_indicator.setStyleSheet("background-color: #95a5a6; border-radius: 6px;")
            self.llm_indicator.setToolTip("LLM адключаны")
            self.llm_status.setText("❌ LLM адключаны")
            self.llm_status.setStyleSheet("font-size: 14px; color: #95a5a6;")

    def load_settings(self):
        """Загрузка налад"""
        config_file = Path("llm_config.json")
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

            if config.get('enabled'):
                provider = config['provider'].title()
                # Апрацоўка custom endpoint
                if config.get('use_custom_endpoint', False):
                    self.provider_combo.setCurrentText('Custom')
                    self.custom_url_input.setText(config.get('custom_endpoint', ''))
                else:
                    self.provider_combo.setCurrentText(provider)
                
                self.model_combo.setCurrentText(config['model'])
                self.temperature_spin.setValue(config.get('temperature', 0.5))
                self.tokens_spin.setValue(config.get('max_tokens', 1000))
                
                # Калі ёсць custom endpoint у канфігурацыі
                if config.get('custom_endpoint'):
                    self.custom_url_input.setText(config['custom_endpoint'])

    def update_stats(self):
        """Абнаўленне статыстыкі"""
        if self.engine:
            stats = self.engine.get_stats()
            stats_text = (
                f"📚 Фактаў: {stats['facts']:,}\n"
                f"🔍 Слоў: {stats['indexed_words']:,}\n"
                f"🔗 Асацыяцый: {stats['associations']}\n"
                f"🎯 Мэтаў: {stats['goals']}"
            )
            self.stats_label.setText(stats_text)

    def on_provider_changed(self, provider):
        """Змена provider"""
        if provider == 'Адключаны':
            self.model_combo.setEnabled(False)
            self.custom_url_input.setEnabled(False)
        elif provider == 'Custom':
            self.model_combo.setEnabled(True)
            self.custom_url_input.setEnabled(True)
            self.custom_url_input.setFocus()
        else:
            self.model_combo.setEnabled(True)
            self.custom_url_input.setEnabled(False)

    def on_llm_check_changed(self, state):
        """Змена опцыі LLM"""
        if state == Qt.Checked and not self.llm.enabled:
            QMessageBox.warning(
                self,
                "LLM адключаны",
                "LLM не ўключаны!\n\n"
                "1. Абярыце provider\n"
                "2. Націсніце 'Уключыць LLM'\n\n"
                "Або выкарыстоўвайце:\n./run.sh llm-on"
            )
            self.use_llm_check.setChecked(False)

    def enable_llm(self):
        """Уключэнне LLM"""
        provider = self.provider_combo.currentText().lower()
        if provider == 'адключаны':
            QMessageBox.warning(self, "Памылка", "Абярыце provider!")
            return

        model = self.model_combo.currentText()

        try:
            # Калі абраны Custom provider
            if provider == 'custom':
                url = self.custom_url_input.text().strip()
                if not url:
                    QMessageBox.warning(self, "Памылка", "Увядзіце URL кастомнага endpoint!")
                    return
                self.llm.set_custom_endpoint(url)
                self.llm.enable_custom_endpoint(url)
                QMessageBox.information(
                    self,
                    "LLM уключаны",
                    f"✅ LLM уключаны:\nCustom endpoint\n\n"
                    f"URL: {url}\n"
                    f"Model: {model}"
                )
            else:
                self.llm.enable(provider, model)
                QMessageBox.information(
                    self,
                    "LLM уключаны",
                    f"✅ LLM уключаны:\n{provider}/{model}\n\n"
                    f"Endpoint: {self.llm.endpoints.get(provider, 'unknown')}"
                )
            
            # Абнаўленне індыкатара
            self.update_llm_indicator()
        except Exception as e:
            QMessageBox.critical(self, "Памылка", f"Не ўдалося ўключыць LLM:\n{e}")

    def enable_custom_endpoint(self):
        """Уключэнне кастомнага endpoint"""
        url = self.custom_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Памылка", "Увядзіце URL кастомнага endpoint!")
            return

        model = self.model_combo.currentText()

        try:
            self.llm.set_custom_endpoint(url)
            self.llm.enable_custom_endpoint(url)
            
            # Абнаўленне індыкатара
            self.update_llm_indicator()

            QMessageBox.information(
                self,
                "Custom endpoint уключаны",
                f"✅ Кастомны endpoint уключаны:\n\n"
                f"URL: {url}\n"
                f"Model: {model}\n\n"
                f"Цяпер выкарыстоўваецца для ўсіх запытаў."
            )
        except Exception as e:
            QMessageBox.critical(self, "Памылка", f"Не ўдалося ўключыць custom endpoint:\n{e}")

    def disable_custom_endpoint(self):
        """Адключэнне кастомнага endpoint"""
        try:
            self.llm.disable_custom_endpoint()
            
            # Абнаўленне індыкатара
            self.update_llm_indicator()
            
            QMessageBox.information(
                self,
                "Custom endpoint адключаны",
                "✅ Кастомны endpoint адключаны.\n\n"
                "Цяпер выкарыстоўваецца provider па змаўчанні."
            )
        except Exception as e:
            QMessageBox.critical(self, "Памылка", f"Не ўдалося адключыць custom endpoint:\n{e}")

    def test_llm(self):
        """Тэставанне LLM"""
        if not self.llm.enabled:
            QMessageBox.warning(self, "Памылка", "Спачатку ўключыце LLM!")
            return

        self.statusBar.showMessage("Тэставанне LLM...")
        
        try:
            facts = [
                "Кастусь Каліноўскі нарадзіўся ў 1838 годзе",
                "Ён быў кіраўніком паўстання 1863 года",
                "Выдаваў газету «Мужыцкая праўда»",
            ]
            
            answer = self.llm.generate("Хто такі Кастусь Каліноўскі?", facts)
            
            QMessageBox.information(
                self,
                "Тэст паспяховы",
                f"✅ LLM адказаў:\n\n{answer[:500]}..."
            )
            
            self.statusBar.showMessage("Гатова")
        except Exception as e:
            QMessageBox.critical(self, "Памылка", f"Тэст не ўдаўся:\n{e}")

    def search(self):
        """Пошук"""
        question = self.search_input.text().strip()
        if not question:
            return

        use_llm = self.use_llm_check.isChecked() and self.llm.enabled

        # Блакіроўка
        self.search_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.statusBar.showMessage("Пошук...")

        # Запуск у асобным патоцы з кантэкстам размовы
        self.search_worker = SearchWorker(
            self.engine, 
            self.llm, 
            question, 
            use_llm,
            self.conversation_context
        )
        self.search_worker.result_ready.connect(self.on_search_result)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.start()

        # Даданне ў гісторыю
        self.add_to_history(question)

    def on_search_result(self, result):
        """Апрацоўка выніку пошуку"""
        self.results_text.setText(result)
        
        # Даданне ў кантэкст размовы (пытанне + адказ)
        question = self.search_input.text().strip()
        self.conversation_context.append(f"❓ Пытанне: {question}")
        self.conversation_context.append(f"📝 Адказ: {result[:500]}...")
        
        # Абмежаванне кантэксту (апошнія 10 рэплік)
        if len(self.conversation_context) > 10:
            self.conversation_context = self.conversation_context[-10:]
        
        self.search_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.statusBar.showMessage("Гатова")

    def on_search_error(self, error):
        """Апрацоўка памылкі"""
        self.results_text.setText(f"❌ Памылка:\n{error}")
        self.search_btn.setEnabled(True)
        self.progress.setVisible(False)
        self.statusBar.showMessage("Памылка")

    def add_to_history(self, question):
        """Даданне ў гісторыю"""
        self.history.append(question)
        
        # Абмежаванне гісторыі
        if len(self.history) > 50:
            self.history.pop(0)
        
        # Абнаўленне спісу
        self.history_list.clear()
        for q in reversed(self.history):
            item = QListWidgetItem(f"❓ {q}")
            self.history_list.addItem(item)

    def on_history_clicked(self, item):
        """Клік па гісторыі"""
        question = item.text()[2:]  # Выдаліць "❓ "
        self.search_input.setText(question)
        self.search()

    def clear_history(self):
        """Ачыстка гісторыі"""
        self.history.clear()
        self.history_list.clear()

    def clear_results(self):
        """Ачыстка вынікаў"""
        self.results_text.clear()
        self.search_input.clear()

    def clear_conversation_context(self):
        """Ачыстка кантэксту размовы"""
        self.conversation_context.clear()
        self.statusBar.showMessage("Кантэкст размовы ачышчаны")
        QMessageBox.information(
            self,
            "Кантэкст ачышчаны",
            "✅ Гісторыя размовы ачышчана.\nЦяпер можна пачаць новы дыялог."
        )

    def copy_results(self):
        """Капіяванне вынікаў"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.results_text.toPlainText())
        self.statusBar.showMessage("Скапіявана ў буфер абмену")

    def add_book(self):
        """Дадаванне кнігі ў базу"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Абярыце кнігу (тэкставы файл)",
            "",
            "Тэкставыя файлы (*.txt);;Усе файлы (*)"
        )

        if not file_paths:
            return

        for file_path in file_paths:
            try:
                # Загрузка файла
                with open(file_path, 'r', encoding='utf-8') as f:
                    book_text = f.read()

                book_name = Path(file_path).stem

                # Дыялог выбару рэжыму парсінгу
                mode_msg = QMessageBox()
                mode_msg.setIcon(QMessageBox.Question)
                mode_msg.setWindowTitle("Рэжым парсінгу")
                mode_msg.setText(f"Як апрацаваць кнігу '{book_name}'?")
                mode_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                mode_msg.button(QMessageBox.Yes).setText("Па сэнтенцыях")
                mode_msg.button(QMessageBox.No).setText("Па раздзелах")
                mode_msg.setDetailedText(
                    "Па сэнтенцыях:\n"
                    "- Больш дакладныя факты\n"
                    "- Лепшы пошук\n\n"
                    "Па раздзелах:\n"
                    "- Большыя кавалкі тэксту\n"
                    "- Захоўваецца кантэкст раздзела"
                )

                reply = mode_msg.exec_()
                parse_mode = 'sentences' if reply == QMessageBox.Yes else 'chapters'

                # Статус
                self.statusBar.showMessage(f"Апрацоўка кнігі '{book_name}'...")
                QApplication.processEvents()

                # Дадаванне кнігі
                facts_count = self.engine.add_book(book_text, book_name, parse_mode)

                # Абнаўленне спісу кніг
                self.update_books_list()

                QMessageBox.information(
                    self,
                    "Кніга дададзена",
                    f"✅ Кніга '{book_name}' дададзена!\n\n"
                    f"📊 Створана фактаў: {facts_count}\n"
                    f"📁 Рэжым: {parse_mode}"
                )

                self.statusBar.showMessage("Гатова")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Памылка",
                    f"Не ўдалося дадаць кнігу:\n{e}"
                )

    def reindex_books(self):
        """Пераіндэксацыя ўсіх кніг"""
        reply = QMessageBox.question(
            self,
            "Пераіндэксацыя",
            "Пераіндэксаваць усе кнігі?\n\nГэта можа заняць некалькі хвілін.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.statusBar.showMessage("Пераіндэксацыя...")
            self.reindex_btn.setEnabled(False)
            QApplication.processEvents()

            self.engine.reindex_all()

            self.update_books_list()
            self.update_stats()

            QMessageBox.information(
                self,
                "Пераіндэксацыя завершана",
                "✅ Усе кнігі пераіндэксаваны!"
            )

            self.statusBar.showMessage("Гатова")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Памылка",
                f"Памылка пераіндэксацыі:\n{e}"
            )
        finally:
            self.reindex_btn.setEnabled(True)

    def update_books_list(self):
        """Абнаўленне спісу кніг"""
        try:
            books_stats = self.engine.get_books_stats()
            books = books_stats.get('books', [])

            self.books_list.clear()
            for book in books:
                item_text = f"📖 {book['name']} ({book['size_mb']:.2f} MB)"
                self.books_list.addItem(item_text)

            # Статыстыка
            self.books_stats_label.setText(
                f"📚 Кніг: {books_stats.get('books_count', 0)}\n"
                f"💾 Памер: {books_stats.get('total_size_mb', 0):.2f} MB\n"
                f"📝 Фактаў: {books_stats.get('facts_count', 0):,}"
            )
        except Exception as e:
            self.books_stats_label.setText(f"Памылка: {e}")

    def export_results(self):
        """Экспарт вынікаў"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Захаваць вынікі",
            "",
            "Тэкставыя файлы (*.txt);;Усе файлы (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.results_text.toPlainText())
                self.statusBar.showMessage(f"Захавана: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Памылка", f"Не ўдалося захаваць:\n{e}")


def main():
    """Галоўная функцыя"""
    if not PYQT_AVAILABLE:
        print("="*80)
        print("❌ PyQt5 не знойдзены!")
        print("="*80)
        print("\nУсталюйце PyQt5:")
        print("  pip install PyQt5")
        print("\nАбо выкарыстоўвайце кансольную версію:")
        print("  ./run.sh run")
        print("="*80)
        return

    app = QApplication(sys.argv)
    
    # Ствараем і паказваем акно
    window = BelEtonGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
