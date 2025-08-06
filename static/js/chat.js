// static/js/chat.js

document.addEventListener('DOMContentLoaded', function() {
    const currentUserUsername = JSON.parse(document.getElementById('current-user-username').textContent);
    const chatLog = document.querySelector('#chat-log');
    const messageInput = document.querySelector('#chat-message-input');
    const messageSubmit = document.querySelector('#chat-message-submit');
    const chatInputContainer = document.querySelector('#chat-input-container');
    const chatRoomName = document.querySelector('#chat-room-name');

    let chatSocket = null;

    function scrollToBottom() {
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // --- NOVA FUNÇÃO PARA RENDERIZAR UMA MENSAGEM ---
    function renderMessage(data) {
        const messageContainer = document.createElement('div');
        const messageBubble = document.createElement('div');
        const userElement = document.createElement('p');
        const textElement = document.createElement('p');
        const timeElement = document.createElement('p');

        messageContainer.classList.add('d-flex', 'mb-3');
        messageBubble.classList.add('p-2', 'rounded');
        messageBubble.style.maxWidth = '80%';
        userElement.classList.add('mb-1', 'small');
        textElement.classList.add('mb-0');
        timeElement.classList.add('mb-0', 'text-end', 'small', 'opacity-75', 'mt-1');

        userElement.innerHTML = `<strong>${data.user}</strong>`;
        textElement.textContent = data.message;
        timeElement.textContent = data.timestamp; // <-- Usa o timestamp completo

        // Esta comparação pode precisar de ajuste se o nome completo for diferente do username
        if (data.user === currentUserUsername || data.user === document.querySelector('a.nav-link.dropdown-toggle').textContent.trim().replace('Olá, ','')) {
            messageContainer.classList.add('justify-content-end');
            messageBubble.classList.add('bg-primary', 'text-white');
        } else {
            messageContainer.classList.add('justify-content-start');
            messageBubble.classList.add('bg-light', 'text-dark');
        }

        messageBubble.appendChild(userElement);
        messageBubble.appendChild(textElement);
        messageBubble.appendChild(timeElement);
        messageContainer.appendChild(messageBubble);
        chatLog.appendChild(messageContainer);
    }

    // --- NOVA FUNÇÃO PARA CARREGAR O HISTÓRICO ---
    async function loadChatHistory(conversaId) {
        chatLog.innerHTML = '<p class="text-center text-muted">A carregar histórico...</p>';
        try {
            const response = await fetch(`/chat/historico/${conversaId}/`);
            const data = await response.json();
            
            chatLog.innerHTML = ''; // Limpa a mensagem de "a carregar"
            
            if (data.historico && data.historico.length > 0) {
                data.historico.forEach(msg => renderMessage(msg));
            } else {
                chatLog.innerHTML = '<p id="chat-empty-message" class="text-center text-muted mt-5">Nenhuma mensagem ainda. Inicie a conversa!</p>';
            }
            scrollToBottom();
        } catch (error) {
            console.error('Erro ao carregar o histórico:', error);
            chatLog.innerHTML = '<p class="text-center text-danger">Não foi possível carregar o histórico.</p>';
        }
    }

    function connectToChat(conversaId) {
        if (chatSocket) {
            chatSocket.close();
        }
        
        loadChatHistory(conversaId);

        chatSocket = new WebSocket(
            'ws://' + window.location.host + '/ws/chat/' + conversaId + '/'
        );

        chatSocket.onopen = function(e) {
            chatInputContainer.style.display = 'flex';
        };

        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            const emptyMsg = document.querySelector('#chat-empty-message');
            if (emptyMsg) emptyMsg.remove();
            renderMessage(data);
            scrollToBottom();
        };

        chatSocket.onclose = function(e) {
            chatInputContainer.style.display = 'none';
        };
    }

    function sendMessage() {
        const message = messageInput.value;
        if (message.trim() === '' || !chatSocket) return;
        chatSocket.send(JSON.stringify({'message': message}));
        messageInput.value = '';
        messageInput.focus();
    }

    messageSubmit.onclick = sendMessage;
    messageInput.onkeyup = function(e) {
        if (e.key === 'Enter') sendMessage();
    };

    const urlParams = new URLSearchParams(window.location.search);
    const conversaId = urlParams.get('conversa_id');

    if (conversaId) {
        connectToChat(conversaId);
        const activeLink = document.querySelector(`a[href="?conversa_id=${conversaId}"]`);
        if (activeLink) {
            chatRoomName.textContent = activeLink.textContent.trim();
        }
    }
});