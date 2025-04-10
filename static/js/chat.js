// static/js/chat.js
document.addEventListener('DOMContentLoaded', function() {
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const chatMessages = document.getElementById('chat-messages');
    const newChatButton = document.getElementById('new-chat-btn');
    const conversationsList = document.getElementById('conversations-list');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const logoutButton = document.getElementById('logout-btn');

    let currentConversationId = null;
    let token = localStorage.getItem('token');

    // Comprueba si el usuario está autenticado
    function checkAuth() {
        if (!token) {
            document.getElementById('auth-container').style.display = 'flex';
            document.getElementById('chat-container').style.display = 'none';
        } else {
            document.getElementById('auth-container').style.display = 'none';
            document.getElementById('chat-container').style.display = 'flex';
            loadUserInfo();
            loadConversations();
        }
    }

    // Carga la información del usuario
    async function loadUserInfo() {
        try {
            const response = await fetch('/api/v1/users/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                document.getElementById('user-name').textContent = userData.username;
            } else {
                // Token inválido o expirado
                localStorage.removeItem('token');
                checkAuth();
            }
        } catch (error) {
            console.error('Error al cargar información del usuario:', error);
        }
    }

    // Carga las conversaciones del usuario
    async function loadConversations() {
        try {
            const response = await fetch('/api/v1/conversations', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const conversations = await response.json();
                renderConversations(conversations);

                // Si hay conversaciones, carga la primera
                if (conversations.length > 0 && !currentConversationId) {
                    loadConversation(conversations[0].id);
                } else if (conversations.length === 0) {
                    chatMessages.innerHTML = `
                        <div class="welcome-message" style="text-align: center; margin-top: 50px;">
                            <h2>¡Bienvenido al ChatBot!</h2>
                            <p>Inicia una nueva conversación para comenzar.</p>
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Error al cargar conversaciones:', error);
        }
    }

    // Renderiza la lista de conversaciones en el sidebar
    function renderConversations(conversations) {
        conversationsList.innerHTML = '';

        conversations.forEach(conv => {
            const conversationItem = document.createElement('div');
            conversationItem.classList.add('conversation-item');
            conversationItem.dataset.id = conv.id;

            if (currentConversationId === conv.id) {
                conversationItem.classList.add('active');
            }

            conversationItem.innerHTML = `
                <i class="fas fa-comment"></i>
                <span>${conv.title}</span>
            `;

            conversationItem.addEventListener('click', () => {
                loadConversation(conv.id);
            });

            conversationsList.appendChild(conversationItem);
        });
    }

    // Carga una conversación específica
    async function loadConversation(conversationId) {
        currentConversationId = conversationId;

        // Actualiza la clase activa en la lista de conversaciones
        document.querySelectorAll('.conversation-item').forEach(item => {
            if (item.dataset.id == conversationId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        try {
            const response = await fetch(`/api/v1/conversations/${conversationId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const conversation = await response.json();
                renderMessages(conversation.messages);
            }
        } catch (error) {
            console.error('Error al cargar la conversación:', error);
        }
    }

    // Renderiza los mensajes de una conversación
    function renderMessages(messages) {
        chatMessages.innerHTML = '';

        messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');
            messageElement.classList.add(message.is_user ? 'user-message' : 'bot-message');

            const timestamp = new Date(message.timestamp);
            const formattedTime = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            messageElement.innerHTML = `
                <div class="message-content">${message.content}</div>
                <div class="message-time">${formattedTime}</div>
            `;

            chatMessages.appendChild(messageElement);
        });

        // Scroll al último mensaje
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Envía un mensaje al chatbot
    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        // Limpia el input
        messageInput.value = '';

        // Añade el mensaje del usuario al chat
        const userMessageElement = document.createElement('div');
        userMessageElement.classList.add('message', 'user-message');

        const now = new Date();
        const formattedTime = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        userMessageElement.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time">${formattedTime}</div>
        `;

        chatMessages.appendChild(userMessageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: currentConversationId
                })
            });

            if (response.ok) {
                const data = await response.json();

                // Si es una nueva conversación, actualiza el ID y recarga la lista
                if (currentConversationId !== data.conversation_id) {
                    currentConversationId = data.conversation_id;
                    loadConversations();
                }

                // Añade la respuesta del bot
                const botMessageElement = document.createElement('div');
                botMessageElement.classList.add('message', 'bot-message');

                botMessageElement.innerHTML = `
                    <div class="message-content">${data.response}</div>
                    <div class="message-time">${formattedTime}</div>
                `;

                chatMessages.appendChild(botMessageElement);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        } catch (error) {
            console.error('Error al enviar mensaje:', error);
        }
    }

    // Crea una nueva conversación
    async function createNewConversation() {
        try {
            const response = await fetch('/api/v1/conversations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    title: 'Nueva conversación'
                })
            });

            if (response.ok) {
                const newConversation = await response.json();
                currentConversationId = newConversation.id;
                loadConversations();

                // Limpia el área de mensajes
                chatMessages.innerHTML = '';
            }
        } catch (error) {
            console.error('Error al crear nueva conversación:', error);
        }
    }

    // Iniciar sesión
    async function login(username, password) {
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            const response = await fetch('/api/v1/users/login/access-token', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                token = data.access_token;
                localStorage.setItem('token', token);
                checkAuth();
            } else {
                alert('Usuario o contraseña incorrectos');
            }
        } catch (error) {
            console.error('Error al iniciar sesión:', error);
        }
    }

    // Registrar usuario
    async function register(username, email, password) {
        try {
            const response = await fetch('/api/v1/users/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    email: email,
                    password: password
                })
            });

            if (response.ok) {
                alert('Usuario registrado correctamente. Por favor, inicia sesión.');
                // Cambiar a la pestaña de login
                loginTab.click();
            } else {
                const error = await response.json();
                alert(`Error al registrar: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error al registrar usuario:', error);
        }
    }

    // Event Listeners

    // Enviar mensaje con click o tecla Enter
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Nueva conversación
    newChatButton.addEventListener('click', createNewConversation);

    // Cambiar entre tabs de login y registro
    loginTab.addEventListener('click', function() {
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
        loginForm.style.display = 'flex';
        registerForm.style.display = 'none';
    });

    registerTab.addEventListener('click', function() {
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
        registerForm.style.display = 'flex';
        loginForm.style.display = 'none';
    });

    // Submit de formularios
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        login(username, password);
    });

    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('register-username').value;
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        register(username, email, password);
    });

    // Cerrar sesión
    logoutButton.addEventListener('click', function() {
        localStorage.removeItem('token');
        token = null;
        checkAuth();
    });

    // Inicializar la interfaz
    checkAuth();
});