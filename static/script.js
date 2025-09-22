// HTTP Chat connection (substitui WebSocket para Vercel)
let isConnected = true;
let artifacts = [];
let conversations = {};
let currentConversationId = null;
let currentUser = localStorage.getItem('currentUser');

// Initialize HTTP connection (substitui WebSocket)
function initConnection() {
    console.log('🔗 [CONEXÃO] Sistema HTTP inicializado');
    isConnected = true;
    updateSendButton();
    
    // Test connection
    testConnection();
}

// Test if API is working
async function testConnection() {
    try {
        const response = await fetch('/api/health');
        if (response.ok) {
            console.log('✅ [CONEXÃO] API funcionando corretamente');
            isConnected = true;
        } else {
            console.log('⚠️ [CONEXÃO] API com problemas');
            isConnected = false;
        }
    } catch (error) {
        console.error('❌ [CONEXÃO] Erro ao testar API:', error);
        isConnected = false;
    }
    updateSendButton();
}

// Handle incoming messages
function handleMessage(data) {
    hideTypingIndicator();
    
    if (data.type === 'processing') {
        console.log('⚙️ [PROCESSAMENTO] Processando resposta do agente...');
        addMessage('assistant', data.content);
        
        // Process artifacts if present
        if (data.artifacts) {
            console.log('🎨 [ARTEFATOS] Processando artefatos:', data.artifacts); // Debug
            processArtifacts(data.artifacts);
        }
        
        console.log('✅ [PROCESSAMENTO] Resposta processada e salva');
    } else if (data.type === 'response') {
        console.log('💬 [RESPOSTA] Processando resposta final do agente...');
        console.log('🔍 [DEBUG] Tipo de resposta:', data.response_type);
        
        addMessage('assistant', data.content);
        
        // Processar artefatos APENAS se houver resultados e não for conversa
        if (data.results && data.results.length > 0 && data.response_type !== 'conversation') {
            console.log('🎨 [ARTEFATOS] Processando artefatos:', data.results);
            processArtifacts(data.results);
        } else if (data.response_type === 'conversation') {
            console.log('💬 [CONVERSA] Resposta conversacional - sem artefatos');
        }
        
        // Save conversation after assistant response
        saveCurrentConversation();
        
        console.log('✅ [RESPOSTA] Resposta final processada e salva');
    }
    
    // Save conversation
    saveCurrentConversation();
}

// Send message via HTTP (substitui WebSocket)
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || !isConnected) return;
    
    console.log('📤 [ENVIO] Enviando mensagem do usuário:', message);
    
    // Add user message
    addMessage('user', message);
    
    // Save conversation after user message
    saveCurrentConversation();
    
    // Clear input
    input.value = '';
    adjustTextareaHeight(input);
    updateSendButton();
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send via HTTP
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: 'message',
                content: message,
                conversation_id: currentConversationId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log('📨 [RESPOSTA] Recebida via HTTP:', result);
        
        if (result.success && result.data) {
            handleMessage(result.data);
        } else {
            throw new Error(result.error || 'Erro desconhecido na resposta');
        }
        
    } catch (error) {
        console.error('❌ [ERRO] Falha ao enviar mensagem:', error);
        hideTypingIndicator();
        addMessage('assistant', `❌ Erro ao enviar mensagem: ${error.message}`);
    }
    
    console.log('✅ [ENVIO] Mensagem enviada e conversa salva');
}

// Add message to chat
function addMessage(sender, content) {
    const messagesContainer = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const time = new Date().toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.innerHTML = `
        <div class="avatar">
            <i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="name">${sender === 'user' ? 'Você' : 'Supervisor'}</span>
                <span class="time">${time}</span>
            </div>
            <div class="message-text">${formatMessageContent(content)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

// Format message content
function formatMessageContent(content) {
    // Handle code blocks
    content = content.replace(/```(\w+)?\n([\s\S]*?)\n```/g, (match, lang, code) => {
        const language = lang || 'plaintext';
        return `<pre><code class="language-${language}">${escapeHtml(code.trim())}</code></pre>`;
    });
    
    // Handle inline code
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Handle bold text
    content = content.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Handle line breaks
    content = content.replace(/\n/g, '<br>');
    
    return content;
}

// Process artifacts from results
function processArtifacts(results) {
    console.log('🎨 [PROCESSAMENTO] Iniciando processamento de artefatos:', results); // Debug
    
    if (!results) {
        console.log('⚠️ [PROCESSAMENTO] Nenhum artefato para processar');
        return;
    }
    
    // Handle both array and single object
    const artifactArray = Array.isArray(results) ? results : [results];
    console.log(`🔢 [PROCESSAMENTO] Processando ${artifactArray.length} artefato(s)`);
    
    artifactArray.forEach((result, index) => {
        console.log(`🎯 [PROCESSAMENTO] Processando artefato ${index + 1}:`, result); // Debug
        
        if (result.type === 'research') {
            const title = result.title || `Pesquisa: ${result.description || result.query || 'Resultado'}`;
            console.log(`🔍 [PESQUISA] Adicionando artefato de pesquisa: ${title}`);
            addArtifact('research', title, result);
        } else if (result.type === 'website') {
            const title = result.title || `Site: ${result.description || 'Website'}`;
            console.log(`🌐 [WEBSITE] Adicionando artefato de website: ${title}`);
            addArtifact('website', title, result);
        } else {
            console.log(`❓ [PROCESSAMENTO] Tipo de artefato desconhecido: ${result.type}`);
        }
    });
    
    console.log('✅ [PROCESSAMENTO] Processamento de artefatos concluído');
    updateArtifactsPanel();
}

// Add artifact
function addArtifact(type, title, data) {
    console.log('🎨 [ARTEFATO] Tentando adicionar:', { type, title, data }); // Debug
    
    // Verificar duplicatas baseadas no título e tipo
    const isDuplicate = artifacts.some(artifact => 
        artifact.type === type && 
        artifact.title === title &&
        JSON.stringify(artifact.data) === JSON.stringify(data)
    );
    
    if (isDuplicate) {
        console.log('⚠️ [ARTEFATO] Duplicata detectada, ignorando:', title);
        return;
    }
    
    // Limitar o número de artefatos para evitar acúmulo excessivo
    const MAX_ARTIFACTS = 20;
    if (artifacts.length >= MAX_ARTIFACTS) {
        console.log(`🧹 [ARTEFATO] Limite de ${MAX_ARTIFACTS} artefatos atingido, removendo os mais antigos`);
        artifacts = artifacts.slice(0, MAX_ARTIFACTS - 1);
    }
    
    const artifact = {
        id: Date.now() + Math.random(),
        type: type,
        title: title,
        data: data,
        timestamp: new Date().toLocaleString('pt-BR'),
        conversationId: currentConversationId // Associar ao chat atual
    };
    
    artifacts.unshift(artifact);
    updateArtifactsPanel();
    updateArtifactsCounter();
    saveArtifacts();
    
    // Always show artifacts panel
    const panel = document.getElementById('artifactsPanel');
    if (!panel.classList.contains('open')) {
        panel.classList.add('open');
    }
    
    console.log('✅ [ARTEFATO] Adicionado com sucesso. Total:', artifacts.length);
}

// Update artifacts panel
function updateArtifactsPanel() {
    const content = document.getElementById('artifactsContent');
    
    if (artifacts.length === 0) {
        content.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>Nenhum artefato disponível</p>
                <small>Os artefatos aparecerão aqui quando os agentes gerarem resultados</small>
            </div>
        `;
        return;
    }
    
    content.innerHTML = artifacts.map(artifact => `
        <div class="artifact-item" onclick="viewArtifact(${artifact.id})">
            <div class="artifact-title">${artifact.title}</div>
            <div class="artifact-type">${artifact.type === 'research' ? '🔍 Pesquisa' : '💻 Website'}</div>
            <div class="artifact-time">${artifact.timestamp}</div>
        </div>
    `).join('');
}

// Update artifacts counter
function updateArtifactsCounter() {
    const counter = document.getElementById('artifactsCount');
    if (counter) {
        counter.textContent = artifacts.length;
        if (artifacts.length === 0) {
            counter.style.display = 'none';
        } else {
            counter.style.display = 'flex';
        }
    }
}

// View artifact details
function viewArtifact(id) {
    const artifact = artifacts.find(a => a.id === id);
    if (!artifact) return;
    
    const modal = document.getElementById('artifactModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');
    
    title.textContent = artifact.title;
    
    if (artifact.type === 'research') {
        body.innerHTML = `
            <h4>Resultados da Pesquisa</h4>
            <div style="margin: 15px 0;">
                <h5>Consulta:</h5>
                <p>${artifact.data.query}</p>
            </div>
            <div style="margin: 15px 0;">
                <h5>Resultados:</h5>
                <div style="background: #40414f; padding: 15px; border-radius: 6px;">
                    ${formatMessageContent(artifact.data.results)}
                </div>
            </div>
            ${artifact.data.sources ? `
                <div style="margin: 15px 0;">
                    <h5>Fontes:</h5>
                    <ul>
                        ${artifact.data.sources.map(source => 
                            `<li><a href="${source}" target="_blank">${source}</a></li>`
                        ).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
    } else if (artifact.type === 'website') {
        // Preparar o conteúdo HTML para o iframe
        let htmlContent = '';
        
        if (artifact.data.artifacts && typeof artifact.data.artifacts === 'object') {
            // Se tem estrutura de código separado (html, css, js)
            const code = artifact.data.artifacts;
            htmlContent = `
                <!DOCTYPE html>
                <html lang="pt-BR">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>${artifact.title || 'Website Preview'}</title>
                    <style>${code.css || ''}</style>
                </head>
                <body>
                    ${code.html || ''}
                    <script>${code.js || ''}</script>
                </body>
                </html>
            `;
        } else if (artifact.data.content) {
            // Se tem conteúdo HTML direto
            htmlContent = artifact.data.content;
        } else {
            htmlContent = '<p>Erro: Conteúdo do website não encontrado.</p>';
        }
        
        // Criar o iframe com blob URL para melhor compatibilidade
        const iframeId = `iframe_${artifact.id}`;
        
        body.innerHTML = `
            <h4>Pré-visualização do Website</h4>
            <div style="margin: 15px 0;">
                <h5>Descrição:</h5>
                <p>${artifact.data.description}</p>
            </div>
            <div style="margin: 15px 0; position: relative;">
                <iframe id="${iframeId}" 
                        style="width: 100%; height: 450px; border: 1px solid #ddd; border-radius: 8px; background: white;"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals">
                </iframe>
                <div style="position: absolute; top: 5px; right: 5px; background: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px;">
                    Preview
                </div>
            </div>
            <div style="margin: 15px 0;">
                <button onclick="previewWebsite(${artifact.id})" style="
                    background: #5436da;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    margin-right: 10px;
                    font-size: 14px;
                ">
                    <i class="fas fa-external-link-alt"></i> Abrir em Nova Aba
                </button>
                <button onclick="downloadWebsite(${artifact.id})" style="
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                ">
                    <i class="fas fa-download"></i> Baixar
                </button>
            </div>
        `;
        
        // Carregar o conteúdo no iframe após um pequeno delay
        setTimeout(() => {
            const iframe = document.getElementById(iframeId);
            if (iframe) {
                try {
                    // Usar blob URL para carregar o conteúdo
                    const blob = new Blob([htmlContent], { type: 'text/html' });
                    const url = URL.createObjectURL(blob);
                    
                    iframe.onload = function() {
                        console.log('✅ [MODAL] Website carregado no iframe do modal');
                        // Limpar o URL do blob após o carregamento
                        setTimeout(() => URL.revokeObjectURL(url), 1000);
                    };
                    
                    iframe.onerror = function() {
                        console.error('❌ [MODAL] Erro ao carregar website no iframe');
                        iframe.srcdoc = '<p style="padding: 20px; text-align: center;">Erro ao carregar preview</p>';
                    };
                    
                    iframe.src = url;
                    
                } catch (error) {
                    console.error('❌ [MODAL] Erro ao criar blob URL:', error);
                    // Fallback: usar srcdoc
                    iframe.srcdoc = htmlContent;
                }
            }
        }, 100);
    }
    
    modal.classList.add('open');
}

// Preview website
function previewWebsite(id) {
    const artifact = artifacts.find(a => a.id === id);
    if (!artifact || artifact.type !== 'website') return;
    
    console.log('🌐 [PREVIEW] Iniciando preview do website:', artifact);
    
    // Verificar se os dados do artefato existem
    let htmlContent = '';
    
    if (artifact.data.artifacts && typeof artifact.data.artifacts === 'object') {
        // Se tem estrutura de código separado (html, css, js)
        const code = artifact.data.artifacts;
        htmlContent = `
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${artifact.title || 'Website Preview'}</title>
                <style>${code.css || ''}</style>
            </head>
            <body>
                ${code.html || ''}
                <script>${code.js || ''}</script>
            </body>
            </html>
        `;
    } else if (artifact.data.content) {
        // Se tem conteúdo HTML direto
        htmlContent = artifact.data.content;
    } else {
        console.error('❌ [PREVIEW] Dados do artefato inválidos:', artifact.data);
        alert('Erro: Não foi possível carregar o conteúdo do website.');
        return;
    }
    
    try {
        const blob = new Blob([htmlContent], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        
        const newWindow = window.open(url, '_blank');
        
        // Limpar o URL do blob após um tempo
        setTimeout(() => {
            URL.revokeObjectURL(url);
            console.log('✅ [PREVIEW] Website carregado com sucesso e URL limpo');
        }, 2000);
        
        if (!newWindow) {
            console.error('❌ [PREVIEW] Popup bloqueado pelo navegador');
            alert('Por favor, permita popups para visualizar o website.');
        }
        
    } catch (error) {
        console.error('❌ [PREVIEW] Erro ao criar preview:', error);
        alert('Erro ao criar preview do website.');
    }
}

// Download website
function downloadWebsite(id) {
    const artifact = artifacts.find(a => a.id === id);
    if (!artifact || artifact.type !== 'website') return;
    
    // Verificar se os dados do artefato existem
    let htmlContent = '';
    let filename = 'website.html';
    
    if (artifact.data.artifacts && typeof artifact.data.artifacts === 'object') {
        // Se tem estrutura de código separado (html, css, js)
        const code = artifact.data.artifacts;
        htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${artifact.title || 'Website'}</title>
                <style>${code.css || ''}</style>
            </head>
            <body>
                ${code.html || ''}
                <script>${code.js || ''}</script>
            </body>
            </html>
        `;
    } else if (artifact.data.content) {
        // Se tem conteúdo HTML direto
        htmlContent = artifact.data.content;
    } else {
        console.error('❌ [DOWNLOAD] Dados do artefato inválidos:', artifact.data);
        alert('Erro: Não foi possível baixar o website.');
        return;
    }
    
    // Gerar nome do arquivo baseado no título
    if (artifact.title) {
        filename = artifact.title.toLowerCase()
            .replace(/[^a-z0-9]/g, '_')
            .replace(/_+/g, '_')
            .replace(/^_|_$/g, '') + '.html';
    }
    
    // Criar e baixar o arquivo
    const blob = new Blob([htmlContent], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('✅ [DOWNLOAD] Website baixado:', filename);
}

// Toggle artifacts panel
function toggleArtifacts() {
    const panel = document.getElementById('artifactsPanel');
    panel.classList.toggle('open');
    console.log('🎨 [PAINEL] Painel de artefatos', panel.classList.contains('open') ? 'aberto' : 'fechado');
}

// Close modal
function closeModal() {
    document.getElementById('artifactModal').classList.remove('open');
}

// UI Helpers
function showTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'none';
}

function scrollToBottom() {
    const container = document.getElementById('messages');
    container.scrollTop = container.scrollHeight;
}

function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function updateSendButton() {
    const sendButton = document.getElementById('sendButton');
    const messageInput = document.getElementById('messageInput');
    
    if (sendButton && messageInput) {
        const hasMessage = messageInput.value.trim().length > 0;
        const canSend = isConnected && hasMessage;
        
        sendButton.disabled = !canSend;
        sendButton.style.opacity = canSend ? '1' : '0.5';
    }
}

function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

function startNewChat() {
    const messages = document.getElementById('messages');
    messages.innerHTML = `
        <div class="message assistant">
            <div class="avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="name">Supervisor</span>
                    <span class="time">Agora</span>
                </div>
                <div class="message-text">
                    Olá! Sou o supervisor de agentes especializados. Posso ajudar você com:
                    <br><br>
                    🔍 <strong>Pesquisas</strong> - Busco informações atualizadas na web<br>
                    💻 <strong>Desenvolvimento Web</strong> - Crio sites com JavaScript puro<br><br>
                    O que você gostaria de fazer?
                </div>
            </div>
        </div>
    `;
    
    // Clear artifacts from current conversation only
    console.log('🆕 [NOVO CHAT] Limpando artefatos da conversa atual...');
    artifacts = [];
    updateArtifactsPanel();
    updateArtifactsCounter();
    saveArtifacts();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Persistence functions
function saveCurrentConversation() {
    if (!currentUser) return;
    if (!currentConversationId) {
        currentConversationId = Date.now().toString();
    }
    
    const messages = Array.from(document.getElementById('messages').children)
        .filter(msg => !msg.classList.contains('typing-indicator'))
        .map(msg => ({
            type: msg.classList.contains('user') ? 'user' : 'assistant',
            content: msg.querySelector('.message-text').innerHTML,
            timestamp: msg.querySelector('.time').textContent
        }));
    
    // Get title from first user message or use default
    let title = 'Nova Conversa';
    const firstUserMessage = messages.find(msg => msg.type === 'user');
    if (firstUserMessage) {
        const textContent = firstUserMessage.content.replace(/<[^>]*>/g, ''); // Remove HTML tags
        title = textContent.length > 50 ? textContent.substring(0, 50) + '...' : textContent;
    }
    
    conversations[currentConversationId] = {
        id: currentConversationId,
        title: title,
        messages: messages,
        timestamp: new Date().toISOString()
    };
    
    localStorage.setItem(`${currentUser}_conversations`, JSON.stringify(conversations));
    updateChatHistory();
}

function saveArtifacts() {
    if (currentUser) {
        localStorage.setItem(`${currentUser}_artifacts`, JSON.stringify(artifacts));
    }
}

function loadUserData() {
    currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
        const savedArtifacts = localStorage.getItem(`${currentUser}_artifacts`);
        artifacts = savedArtifacts ? JSON.parse(savedArtifacts) : [];
        const savedConversations = localStorage.getItem(`${currentUser}_conversations`);
        conversations = savedConversations ? JSON.parse(savedConversations) : {};
        loadConversations();
    }
}

function loadConversations() {
    updateChatHistory();
}

function loadArtifacts() {
    const saved = localStorage.getItem('artifacts');
    if (saved) {
        try {
            const loadedArtifacts = JSON.parse(saved);
            console.log('📂 [PERSISTÊNCIA] Carregando artefatos salvos:', loadedArtifacts.length);
            artifacts = loadedArtifacts;
            updateArtifactsPanel();
            updateArtifactsCounter();
        } catch (e) {
            console.error('❌ [PERSISTÊNCIA] Erro ao carregar artefatos:', e);
            artifacts = [];
        }
    }
}

// Função para limpar artefatos antigos
function clearOldArtifacts() {
    if (artifacts.length === 0) {
        console.log('ℹ️ [LIMPEZA] Nenhum artefato para limpar');
        return;
    }
    
    const count = artifacts.length;
    console.log(`🧹 [LIMPEZA] Limpando ${count} artefato(s)...`);
    
    artifacts = [];
    localStorage.removeItem('artifacts');
    updateArtifactsPanel();
    updateArtifactsCounter();
    
    // Feedback visual
    const content = document.getElementById('artifactsContent');
    content.innerHTML = `
        <div class="empty-state">
            <i class="fas fa-check-circle" style="color: #28a745;"></i>
            <p>Artefatos limpos com sucesso!</p>
            <small>${count} artefato(s) foram removidos</small>
        </div>
    `;
    
    // Voltar ao estado normal após 2 segundos
    setTimeout(() => {
        updateArtifactsPanel();
    }, 2000);
    
    console.log('✅ [LIMPEZA] Artefatos limpos com sucesso');
}

// Função para limpar todos os dados persistidos
function clearAllData() {
    console.log('🧹 [LIMPEZA] Limpando todos os dados...');
    localStorage.clear();
    artifacts = [];
    conversations = {};
    currentConversationId = null;
    updateArtifactsPanel();
    updateArtifactsCounter();
    updateChatHistory();
    startNewChat();
    console.log('✅ [LIMPEZA] Todos os dados limpos com sucesso');
}

function createNewConversation() {
    saveCurrentConversation();
    currentConversationId = Date.now().toString();
    startNewChat();
    updateChatHistory();
}

function loadConversation(id) {
    const conversation = conversations[id];
    if (!conversation) return;
    
    currentConversationId = id;
    const messagesContainer = document.getElementById('messages');
    messagesContainer.innerHTML = '';
    
    conversation.messages.forEach(msg => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${msg.type}`;
        messageDiv.innerHTML = `
            <div class="avatar">
                <i class="fas fa-${msg.type === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="name">${msg.type === 'user' ? 'Você' : 'Supervisor'}</span>
                    <span class="time">${msg.timestamp}</span>
                </div>
                <div class="message-text">${msg.content}</div>
            </div>
        `;
        messagesContainer.appendChild(messageDiv);
    });
    
    updateChatHistory();
    scrollToBottom();
}

function updateChatHistory() {
    const chatHistory = document.getElementById('chatHistory');
    if (!chatHistory) return;
    
    chatHistory.innerHTML = '';
    
    // Sort conversations by timestamp (newest first)
    const sortedConversations = Object.values(conversations)
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    sortedConversations.forEach(conversation => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-item ${conversation.id === currentConversationId ? 'active' : ''}`;
        chatItem.onclick = () => loadConversation(conversation.id);
        
        chatItem.innerHTML = `
            <i class="fas fa-comments"></i>
            <span>${conversation.title}</span>
        `;
        
        chatHistory.appendChild(chatItem);
    });
    
    // Add current conversation if no conversations exist
    if (sortedConversations.length === 0) {
        const chatItem = document.createElement('div');
        chatItem.className = 'chat-item active';
        chatItem.innerHTML = `
            <i class="fas fa-comments"></i>
            <span>Conversa Atual</span>
        `;
        chatHistory.appendChild(chatItem);
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [INICIALIZAÇÃO] Carregando aplicação...');
    
    loadConversations();
    loadArtifacts();
    updateChatHistory();
    updateArtifactsCounter();
    // Initialize connection when page loads
    initConnection();
    
    // Test connection periodically
    setInterval(testConnection, 30000); // Test every 30 seconds
    
    const input = document.getElementById('messageInput');
    input.addEventListener('input', () => updateSendButton());
    
    // Close modal on outside click
    document.getElementById('artifactModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'b') {
            e.preventDefault();
            toggleArtifacts();
        }
    });
    
    // Save conversation before page unload
    window.addEventListener('beforeunload', function() {
        saveCurrentConversation();
    });
    
    console.log('✅ [INICIALIZAÇÃO] Aplicação carregada com sucesso');
});