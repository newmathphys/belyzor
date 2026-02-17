// 💬 JavaScript для БелУзор v0.1 — Беларусь

let conversationHistory = [];
let isProcessing = false;
let currentChatId = null;

// Ініцыялізацыя
document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadLLMStatus();
    loadHistory();
    loadBooks();
    loadEncyclopedias();
    loadDictionaries();
    loadChatsList();
});

// Аўтаматычнае змяненне памеру textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 180) + 'px';
}

// Апрацоўка клавіш
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Адпраўка паведамлення
async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    
    if (!message || isProcessing) return;
    
    // Схаваць прывітанне, паказаць кантэйнер паведамленняў
    document.getElementById('welcome-message').style.display = 'none';
    document.getElementById('messages-container').classList.add('active');
    
    // Даданне паведамлення карыстальніка
    addMessage('user', message);
    
    // Ачыстка поля
    input.value = '';
    input.style.height = 'auto';
    
    // Адпраўка на сервер
    isProcessing = true;
    document.getElementById('btn-send').disabled = true;
    
    // Паказ індыкатара загрузкі
    const loadingId = addLoading();
    
    try {
        const useLLM = document.getElementById('use-llm').checked;
        const showFacts = document.getElementById('show-facts').checked;
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                use_llm: useLLM
            })
        });
        
        if (!response.ok) {
            throw new Error('Памылка сервера');
        }
        
        const data = await response.json();
        
        // Выдаленне індыкатара загрузкі
        removeLoading(loadingId);
        
        // Даданне адказу з крыніцамі
        addMessage('assistant', data.llm_answer, data.facts, showFacts);
        
    } catch (error) {
        removeLoading(loadingId);
        addMessage('assistant', `❌ Памылка: ${error.message}`);
    } finally {
        isProcessing = false;
        document.getElementById('btn-send').disabled = false;
        input.focus();
    }
}

// Даданне паведамлення
function addMessage(role, text, facts = null, showFacts = true) {
    const container = document.getElementById('messages-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    let html = `<h4>${role === 'user' ? '👤 Вы' : '🤖 БелУзор'}</h4>`;
    html += `<div class="message-text">${escapeHtml(text)}</div>`;
    
    // Калі ёсць факты і яны павінны адлюстроўвацца
    if (facts && facts.length > 0 && showFacts && role === 'assistant') {
        html += `<div class="facts-container">`;
        html += `<h5>📚 Крыніцы (${facts.length}): <button class="btn-search-all" onclick="searchAllInGoogle()">🔍 Шукаць усе ў Google</button></h5>`;
        facts.forEach((fact, i) => {
            const googleQuery = encodeURIComponent(fact.substring(0, 100));
            
            // Ачыстка крыніцы ад імёнаў файлаў
            let cleanFact = fact
                .replace(/^\[tom_\d+_clean\]\s*/gi, '')  // Прыбраць [tom_1_clean]
                .replace(/^\[encyclopedia_volume_\d+\]\s*/gi, '')  // Прыбраць [encyclopedia_volume_1]
                .replace(/^\[\d+\]\s*/gi, '')  // Прыбраць [1]
                .replace(/^\d+\.\s*/gi, '')  // Прыбраць 1.
                .trim();
            
            // Вызначэнне крыніцы
            let sourceBadge = '';
            if (fact.match(/tom_\d+_clean/i)) {
                sourceBadge = '<span class="source-badge encyclopedia">📚 Энцыклапедыя</span>';
            } else if (fact.match(/^\[\d\]/) || fact.match(/^\d+\./)) {
                sourceBadge = '<span class="source-badge textbook">📖 Падручнік</span>';
            }
            
            html += `
                <div class="fact-item">
                    <span class="fact-number">[${i+1}]</span>
                    ${sourceBadge}
                    <span class="fact-text">${escapeHtml(cleanFact)}</span>
                    <div class="fact-actions">
                        <button class="btn-search-google" onclick="searchInGoogle('${googleQuery}')">
                            🔍 Google
                        </button>
                    </div>
                </div>
            `;
        });
        html += `</div>`;
    }
    
    contentDiv.innerHTML = html;
    messageDiv.appendChild(contentDiv);
    container.appendChild(messageDiv);
    
    // Пракрутка ўніз
    container.scrollTop = container.scrollHeight;
}

// Пошук у Google
function searchInGoogle(query) {
    window.open(`https://www.google.com/search?q=${query}`, '_blank');
}

// Пошук усіх крыніц у Google
function searchAllInGoogle() {
    const factTexts = document.querySelectorAll('.fact-item .fact-text');
    if (factTexts.length === 0) return;
    
    const queries = Array.from(factTexts).map(el => el.textContent.trim());
    const combinedQuery = encodeURIComponent(queries.slice(0, 3).join(' OR '));
    
    window.open(`https://www.google.com/search?q=${combinedQuery}`, '_blank');
}

// Індыкатар загрузкі
function addLoading() {
    const container = document.getElementById('messages-container');
    const id = 'loading-' + Date.now();
    
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message message-assistant';
    loadingDiv.id = id;
    
    loadingDiv.innerHTML = `
        <div class="message-content">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="loading"></div>
                <span>Пошук адказу па ўзоры кніг...</span>
            </div>
        </div>
    `;
    
    container.appendChild(loadingDiv);
    container.scrollTop = container.scrollHeight;
    
    return id;
}

function removeLoading(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

// Прыклад пытання
function sendExample(question) {
    document.getElementById('message-input').value = question;
    sendMessage();
}

// Новы дыялог
function newChat() {
    // Аўтаматычнае захаванне бягучага дыялогу
    if (currentChatId || document.querySelectorAll('.message').length > 0) {
        saveChat();
    }
    
    document.getElementById('messages-container').innerHTML = '';
    document.getElementById('welcome-message').style.display = 'block';
    conversationHistory = [];
    currentChatId = null;
    
    // Абнаўленне спісу дыялогаў
    loadChatsList();
    
    showMessage('Новы дыялог пачаты');
}

// Ачыстка гісторыі
async function clearHistory() {
    if (!confirm('Сапраўды ачысціць гісторыю дыялогаў?')) return;
    
    try {
        await fetch('/api/history/clear', { method: 'POST' });
        conversationHistory = [];
        document.getElementById('messages-container').innerHTML = '';
        document.getElementById('welcome-message').style.display = 'block';
        currentChatId = null;
        localStorage.removeItem('belUzor_chats');
        showMessage('Гісторыя ачышчана');
    } catch (error) {
        showMessage('Памылка: ' + error.message);
    }
}

// Загрузка статыстыкі
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('stat-facts').textContent = stats.facts.toLocaleString();
        document.getElementById('stat-words').textContent = stats.indexed_words.toLocaleString();
        document.getElementById('stat-books').textContent = stats.books_count;
        
    } catch (error) {
        console.error('Памылка загрузкі статыстыкі:', error);
    }
}

// Загрузка статусу LLM
async function loadLLMStatus() {
    try {
        const response = await fetch('/api/llm/status');
        const status = await response.json();
        
        const indicator = document.getElementById('llm-indicator');
        const text = document.getElementById('llm-text');
        const btnEnable = document.getElementById('btn-llm-enable');
        const btnDisable = document.getElementById('btn-llm-disable');
        
        if (status.enabled) {
            indicator.classList.add('active');
            text.textContent = `${status.provider} / ${status.model}`;
            text.style.color = 'var(--success-color)';
            btnEnable.style.display = 'none';
            btnDisable.style.display = 'block';
        } else {
            indicator.classList.remove('active');
            text.textContent = 'Адключаны';
            text.style.color = 'var(--text-light)';
            btnEnable.style.display = 'block';
            btnDisable.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Памылка загрузкі LLM статусу:', error);
    }
}

// Уключыць LLM
async function enableLLM() {
    openModal();
}

// Адключыць LLM
async function disableLLM() {
    if (!confirm('Сапраўды адключыць LLM?')) return;
    
    try {
        await fetch('/api/llm/disable', { method: 'POST' });
        document.getElementById('use-llm').checked = false;
        showMessage('LLM адключаны');
        loadLLMStatus();
    } catch (error) {
        showMessage('Памылка: ' + error.message);
    }
}

// Модальнае акно
function openModal() {
    document.getElementById('llm-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('llm-modal').classList.remove('active');
}

// Захаванне налад LLM
async function saveLLMSettings() {
    const provider = document.getElementById('llm-provider').value;
    const model = document.getElementById('llm-model').value;
    const customUrl = document.getElementById('llm-custom-url').value;
    
    try {
        const response = await fetch('/api/llm/enable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: provider,
                model: model,
                custom_url: customUrl
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage(result.message);
            document.getElementById('use-llm').checked = true;
            closeModal();
            loadLLMStatus();
        } else {
            showMessage('Памылка: ' + result.error);
        }
        
    } catch (error) {
        showMessage('Памылка: ' + error.message);
    }
}

// Загрузка гісторыі
async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        conversationHistory = data.history || [];
        
        // Калі ёсць гісторыя, паказаць яе
        if (conversationHistory.length > 0) {
            document.getElementById('welcome-message').style.display = 'none';
            document.getElementById('messages-container').classList.add('active');
            
            conversationHistory.forEach(msg => {
                if (msg.role === 'assistant') {
                    addMessage(msg.role, msg.content, msg.facts, true);
                }
            });
        }
        
    } catch (error) {
        console.error('Памылка загрузкі гісторыі:', error);
    }
}

// Загрузка кніг
async function loadBooks() {
    try {
        const response = await fetch('/api/books');
        const data = await response.json();
        
        const booksList = document.getElementById('books-list');
        
        if (data.books && data.books.length > 0) {
            booksList.innerHTML = data.books.map(book => `
                <div class="material-item book-item">
                    <span class="material-icon">📕</span>
                    <span class="material-name">${book.name}</span>
                    <span class="material-size">${book.size_mb} MB</span>
                </div>
            `).join('');
        } else {
            booksList.innerHTML = '<p class="no-items">Кніг няма</p>';
        }
        
    } catch (error) {
        console.error('Памылка загрузкі кніг:', error);
        document.getElementById('books-list').innerHTML = '<p class="error">Памылка загрузкі</p>';
    }
}

// Загрузка энцыклапедый
async function loadEncyclopedias() {
    try {
        const response = await fetch('/api/encyclopedias');
        const data = await response.json();
        
        const encList = document.getElementById('encyclopedia-list');
        
        if (data.encyclopedias && data.encyclopedias.length > 0) {
            encList.innerHTML = data.encyclopedias.map((enc, i) => `
                <div class="material-item encyclopedia-item">
                    <span class="material-icon">📖</span>
                    <span class="material-name">Том ${i+1}</span>
                    <span class="material-size">${enc.size_mb} MB</span>
                </div>
            `).join('');
        } else {
            encList.innerHTML = '<p class="no-items">Энцыклапедый няма</p>';
        }
        
    } catch (error) {
        console.error('Памылка загрузкі энцыклапедый:', error);
        document.getElementById('encyclopedia-list').innerHTML = '<p class="error">Памылка загрузкі</p>';
    }
}

// Загрузка слоўнікаў
async function loadDictionaries() {
    try {
        const response = await fetch('/api/dictionaries');
        const data = await response.json();
        
        const dictList = document.getElementById('dictionaries-list');
        
        if (data.dictionaries && data.dictionaries.length > 0) {
            dictList.innerHTML = data.dictionaries.map(dict => `
                <div class="material-item dictionary-item" onclick="viewDictionary('${dict.name}')" style="cursor: pointer;">
                    <span class="material-icon">📗</span>
                    <span class="material-name">${dict.name}</span>
                    <span class="material-size">${dict.count || ''}</span>
                </div>
            `).join('');
        } else {
            dictList.innerHTML = '<p class="no-items">Слоўнікаў няма</p>';
        }
        
    } catch (error) {
        console.error('Памылка загрузкі слоўнікаў:', error);
        document.getElementById('dictionaries-list').innerHTML = '<p class="error">Памылка загрузкі</p>';
    }
}

// Прагляд слоўніка
async function viewDictionary(dictName) {
    try {
        const modal = document.getElementById('dictionary-modal');
        const title = document.getElementById('dict-title');
        const content = document.getElementById('dictionary-content');
        const countLabel = document.getElementById('dict-count');
        
        title.textContent = dictName;
        content.innerHTML = '<p class="loading">Загрузка...</p>';
        modal.classList.add('active');
        
        const response = await fetch(`/api/dictionaries/${encodeURIComponent(dictName)}`);
        const data = await response.json();
        
        if (data.entries && data.entries.length > 0) {
            window.currentDictionary = data.entries;
            countLabel.textContent = `${data.entries.length} запісаў`;
            renderDictionary(data.entries);
        } else {
            content.innerHTML = '<p class="no-items">Запісаў не знойдзена</p>';
        }
        
    } catch (error) {
        showMessage('Памылка загрузкі слоўніка: ' + error.message);
        closeDictionaryModal();
    }
}

// Рэндэрынг слоўніка
function renderDictionary(entries) {
    const content = document.getElementById('dictionary-content');
    
    if (!entries || entries.length === 0) {
        content.innerHTML = '<p class="no-items">Запісаў не знойдзена</p>';
        return;
    }
    
    content.innerHTML = entries.map(entry => {
        const word = entry.word || '';
        const definition = entry.definition || '';
        
        // Калі ёсць і слова і азначэнне
        if (word && definition) {
            return `
                <div class="dictionary-entry">
                    <div class="entry-word">${escapeHtml(word)}</div>
                    <div class="entry-definition">${escapeHtml(definition)}</div>
                </div>
            `;
        }
        // Калі толькі слова (назва артыкула)
        else if (word) {
            return `
                <div class="dictionary-entry">
                    <div class="entry-word">${escapeHtml(word)}</div>
                </div>
            `;
        }
        // Пусты запіс - прапускаем
        return '';
    }).filter(html => html.trim() !== '').join('');
    
    if (content.innerHTML.trim() === '') {
        content.innerHTML = '<p class="no-items">Запісаў не знойдзена</p>';
    }
}

// Фільтр слоўніка
function filterDictionary() {
    const query = document.getElementById('dict-search').value.toLowerCase();
    
    if (!window.currentDictionary) return;
    
    const filtered = window.currentDictionary.filter(entry => {
        const word = (entry.word || '').toLowerCase();
        const def = (entry.definition || '').toLowerCase();
        return word.includes(query) || def.includes(query);
    });
    
    document.getElementById('dict-count').textContent = `${filtered.length} запісаў`;
    renderDictionary(filtered);
}

// Закрыццё модальнага акна слоўніка
function closeDictionaryModal() {
    const modal = document.getElementById('dictionary-modal');
    modal.classList.remove('active');
    window.currentDictionary = null;
    document.getElementById('dict-search').value = '';
}

// Пераключэнне матэрыялаў
function toggleMaterials(type) {
    const list = document.getElementById(`${type}-list`);
    const icon = document.getElementById(`${type}-icon`);
    
    if (list.style.display === 'none') {
        list.style.display = 'block';
        icon.textContent = '▼';
    } else {
        list.style.display = 'none';
        icon.textContent = '▶';
    }
}

// Загрузка спісу дыялогаў
function loadChatsList() {
    const chats = JSON.parse(localStorage.getItem('belUzor_chats') || '[]');
    const chatsList = document.getElementById('chats-list');
    const chatCount = document.getElementById('chat-count');
    
    chatCount.textContent = `(${chats.length})`;
    
    if (chats.length === 0) {
        chatsList.innerHTML = '<p class="no-chats">Дыялогаў няма</p>';
        return;
    }
    
    // Сартыроўка па часе (новыя зверху)
    const sortedChats = chats.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    chatsList.innerHTML = sortedChats.map((chat, i) => {
        const date = new Date(chat.timestamp).toLocaleString('be-BY', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
        const firstMessage = chat.messages[0]?.content.substring(0, 40) || 'Дыялог';
        
        return `
            <div class="chat-item-sidebar" id="sidebar-chat-${chat.id}">
                <div class="chat-item-sidebar-info" onclick="loadSpecificChat(${chat.id})">
                    <div class="chat-item-title">${firstMessage}${chat.messages[0]?.content.length > 40 ? '...' : ''}</div>
                    <div class="chat-item-meta">
                        <span class="chat-item-date">${date}</span>
                        <span class="chat-item-messages">${chat.messages.length} пав.</span>
                    </div>
                </div>
                <button class="btn-delete-chat-sidebar" onclick="deleteChat(${chat.id})" title="Выдаліць дыялог">
                    🗑️
                </button>
            </div>
        `;
    }).join('');
}

// Загрузка кніг
async function loadBooks() {
    try {
        const response = await fetch('/api/books');
        const data = await response.json();
        
        const booksList = document.getElementById('books-list');
        
        if (data.books && data.books.length > 0) {
            booksList.innerHTML = data.books.map(book => `
                <div class="book-item">
                    <span>📖 ${book.name}</span>
                    <span style="color: rgba(255,255,255,0.5); font-size: 12px;">${book.size_mb} MB</span>
                </div>
            `).join('');
        } else {
            booksList.innerHTML = '<p style="color: rgba(255,255,255,0.5); font-size: 13px;">Кніг няма</p>';
        }
        
    } catch (error) {
        console.error('Памылка загрузкі кніг:', error);
        document.getElementById('books-list').innerHTML = '<p style="color: rgba(255,255,255,0.5); font-size: 13px;">Памылка загрузкі</p>';
    }
}

// Дадаванне кнігі
function addBook() {
    document.getElementById('file-input').click();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async function(e) {
        const bookText = e.target.result;
        const bookName = file.name.replace('.txt', '');
        
        try {
            showMessage(`Апрацоўка кнігі "${bookName}"...`);
            
            // Запампоўка на сервер
            const response = await fetch('/api/books/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    book_text: bookText,
                    book_name: bookName,
                    parse_mode: 'sentences'
                })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showMessage(`✅ Кніга дададзена: ${result.facts_count} фактаў`);
                loadBooks();
                loadStats();
            } else {
                showMessage('Памылка: ' + result.error);
            }
            
        } catch (error) {
            showMessage('Памылка: ' + error.message);
        }
    };
    reader.readAsText(file, 'UTF-8');
    
    // Ачыстка input для паўторнага выбару таго ж файла
    event.target.value = '';
}

// Захаванне дыялогу
function saveChat() {
    const messages = document.querySelectorAll('.message');
    if (messages.length === 0) {
        showMessage('Няма чаго захоўваць');
        return;
    }
    
    const chatData = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        messages: []
    };
    
    messages.forEach(msg => {
        const isUser = msg.classList.contains('message-user');
        const content = msg.querySelector('.message-text').textContent;
        chatData.messages.push({
            role: isUser ? 'user' : 'assistant',
            content: content,
            timestamp: new Date().toISOString()
        });
    });
    
    // Захаванне ў localStorage
    let chats = JSON.parse(localStorage.getItem('belUzor_chats') || '[]');
    chats.push(chatData);
    localStorage.setItem('belUzor_chats', JSON.stringify(chats));
    
    currentChatId = chatData.id;
    showMessage('Дыялог захаваны');
}

// Загрузка дыялогу
function loadChat() {
    const chats = JSON.parse(localStorage.getItem('belUzor_chats') || '[]');

    if (chats.length === 0) {
        showMessage('Захаваных дыялогаў няма');
        return;
    }

    // Стварэнне спісу дыялогаў
    const chatList = chats.map((chat, i) => {
        const date = new Date(chat.timestamp).toLocaleString('be-BY');
        return `
            <div class="chat-item" id="chat-${chat.id}">
                <div class="chat-item-info" onclick="loadSpecificChat(${chat.id})">
                    <strong>Дыялог #${i + 1}</strong><br>
                    <small class="chat-date">${date}</small><br>
                    <small class="chat-messages">${chat.messages.length} паведамленняў</small>
                </div>
                <button class="btn-delete-chat" onclick="deleteChat(${chat.id})" title="Выдаліць дыялог">
                    🗑️
                </button>
            </div>
        `;
    }).join('');

    // Паказ модальнага акна са спісам
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>📂 Загрузка дыялогу</h3>
                <button class="btn-close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body modal-body-scroll">
                ${chatList}
            </div>
            <div class="modal-footer">
                <button class="btn-cancel" onclick="this.closest('.modal').remove()">Закрыць</button>
                <button class="btn-delete-all" onclick="deleteAllChats()">🗑️ Выдаліць усе</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Выдаленне дыялогу
function deleteChat(chatId) {
    if (!confirm('Выдаліць гэты дыялог?')) return;
    
    let chats = JSON.parse(localStorage.getItem('belUzor_chats') || '[]');
    chats = chats.filter(c => c.id !== chatId);
    localStorage.setItem('belUzor_chats', JSON.stringify(chats));
    
    // Абнаўленне спісу ў бакавой панэлі
    loadChatsList();
    
    // Выдаленне з мадальнага акна
    const chatItem = document.getElementById(`chat-${chatId}`);
    if (chatItem) chatItem.remove();
    
    showMessage('Дыялог выдалены');
}

// Выдаленне ўсіх дыялогаў
function deleteAllChats() {
    if (!confirm('Сапраўды выдаліць УСЕ дыялогі?')) return;
    
    localStorage.removeItem('belUzor_chats');
    
    // Зачыненне модальнага акна
    document.querySelector('.modal').remove();
    
    showMessage('Усе дыялогі выдалены');
}

// Загрузка канкрэтнага дыялогу
function loadSpecificChat(chatId) {
    const chats = JSON.parse(localStorage.getItem('belUzor_chats') || '[]');
    const chat = chats.find(c => c.id === chatId);
    
    if (!chat) return;
    
    document.getElementById('messages-container').innerHTML = '';
    document.getElementById('welcome-message').style.display = 'none';
    document.getElementById('messages-container').classList.add('active');
    
    chat.messages.forEach(msg => {
        addMessage(msg.role, msg.content, null, false);
    });
    
    currentChatId = chatId;
    
    // Зачыненне модальнага акна
    document.querySelector('.modal').remove();
    showMessage('Дыялог загружаны');
}

// Захаванне ў localStorage
function saveChatToStorage() {
    if (currentChatId) {
        saveChat();
    }
}

// Экспарт дыялогу
function exportChat() {
    const messages = document.querySelectorAll('.message');
    if (messages.length === 0) {
        showMessage('Няма чаго экспартаваць');
        return;
    }
    
    let text = '🧠🇧🇾 БелУзор v0.1 — Дыялог\n';
    text += '=' .repeat(60) + '\n';
    text += `Дата: ${new Date().toLocaleString('be-BY')}\n`;
    text += '=' .repeat(60) + '\n\n';
    
    messages.forEach(msg => {
        const role = msg.classList.contains('message-user') ? 'Вы' : 'БелУзор';
        const content = msg.querySelector('.message-text').textContent;
        text += `${role}: ${content}\n\n`;
    });
    
    text += '\n' + '=' .repeat(60) + '\n';
    text += 'Працуем па ўзоры давераных кніг\n';
    
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `БелУзор_дыялог_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    showMessage('Дыялог экспартаваны');
}

// Паведамленне
function showMessage(text) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const div = document.createElement('div');
    div.className = 'toast';
    div.textContent = text;
    document.body.appendChild(div);
    
    setTimeout(() => {
        div.style.animation = 'fadeOut 0.3s';
        setTimeout(() => div.remove(), 300);
    }, 3000);
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Даданне анімацый
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(20px); }
    }
`;
document.head.appendChild(style);
