// static/js/chat.js

document.addEventListener('DOMContentLoaded', function() {
    // Seletores de elementos DOM
    const chatLog = document.querySelector('#chat-log');
    const messageInput = document.querySelector('#chat-message-input');
    const messageSubmit = document.querySelector('#chat-message-submit');
    const chatInputContainer = document.querySelector('#chat-input-container');
    const chatRoomName = document.querySelector('#chat-room-name');

    let chatSocket = null;
    let currentConversationId = null;

    // Função para rolar o chat para a última mensagem
    function scrollToBottom() {
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // --- MUDANÇA: Função 'renderMessage' refatorada com Template Literals e 'is_me' ---
    // Agora usa 'data.is_me' vindo do backend para estilizar a mensagem.
    function renderMessage(data) {
        // Remove a mensagem "Nenhuma mensagem ainda" se ela existir
        const emptyMsg = document.querySelector('#chat-empty-message');
        if (emptyMsg) emptyMsg.remove();

        const bubbleClasses = data.is_me ? 'justify-content-end' : 'justify-content-start';
        const messageClasses = data.is_me ? 'bg-primary text-white' : 'bg-light text-dark';
        
        // Usando template literal para criar o HTML de forma mais limpa
        const messageHTML = `
            <div class="d-flex mb-3 ${bubbleClasses}">
                <div class="p-2 rounded ${messageClasses}" style="max-width: 80%;">
                    <p class="mb-1 small"><strong>${data.user}</strong></p>
                    <p class="mb-0" style="word-wrap: break-word;">${data.message}</p>
                    <p class="mb-0 text-end small opacity-75 mt-1">${data.timestamp}</p>
                </div>
            </div>`;
        
        chatLog.insertAdjacentHTML('beforeend', messageHTML);
    }

    function connectToChat(conversaId) {
        // Evita reconexões desnecessárias para a mesma conversa
        if (chatSocket && currentConversationId === conversaId) {
            return;
        }
        currentConversationId = conversaId;

        // Fecha qualquer socket anterior
        if (chatSocket) {
            chatSocket.close();
        }
        
        // --- MUDANÇA: Lógica de carregamento agora é interna do WebSocket ---
        chatLog.innerHTML = '<p class="text-center text-muted">A ligar ao chat...</p>';

        // --- MUDANÇA: Protocolo dinâmico (ws:// ou wss://) para segurança 🔒 ---
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsURL = `${protocol}${window.location.host}/ws/chat/${conversaId}/`;
        
        chatSocket = new WebSocket(wsURL);

        // --- MUDANÇA: Lógica 'onmessage' agora trata o histórico e novas mensagens ---
        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);

            if (data.type === 'message_history') {
                // Limpa a mensagem "A ligar..."
                chatLog.innerHTML = ''; 
                
                if (data.history && data.history.length > 0) {
                    // Renderiza cada mensagem do histórico recebido
                    data.history.forEach(msg => renderMessage(msg));
                } else {
                    // Exibe uma mensagem se não houver histórico
                    chatLog.innerHTML = '<p id="chat-empty-message" class="text-center text-muted mt-5">Nenhuma mensagem ainda. Inicie a conversa!</p>';
                }
            } else {
                // Se não for histórico, é uma nova mensagem em tempo real
                renderMessage(data);
            }
            scrollToBottom();
        };

        chatSocket.onopen = function(e) {
            // Mostra o campo de input apenas quando a conexão estiver pronta
            chatInputContainer.style.display = 'flex';
            messageInput.focus();
        };

        chatSocket.onclose = function(e) {
            console.error('O socket do chat fechou inesperadamente.');
            chatInputContainer.style.display = 'none';
        };
    }

    function sendMessage() {
        const message = messageInput.value;
        if (message.trim() === '' || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) {
            return;
        }
        
        chatSocket.send(JSON.stringify({
            'message': message
        }));
        
        messageInput.value = '';
        messageInput.focus();
    }

    // Event listeners para enviar a mensagem
    messageSubmit.onclick = sendMessage;
    messageInput.onkeyup = function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    };

    // Lógica inicial para pegar o ID da conversa da URL e iniciar o chat
    const urlParams = new URLSearchParams(window.location.search);
    const conversaIdFromURL = urlParams.get('conversa_id');

    if (conversaIdFromURL) {
        connectToChat(conversaIdFromURL);
        
        // Atualiza o nome da sala de chat no cabeçalho
        const activeLink = document.querySelector(`.list-group-item[data-conversa-id="${conversaIdFromURL}"]`);
        if (activeLink) {
            // Pega o nome do contato de um elemento filho para não pegar o "badge"
            const contactName = activeLink.querySelector('.contact-name').textContent;
            chatRoomName.textContent = contactName.trim();
        }
    }
});