/* ==========================================================================
 * ARQUIVO: script.js
 * OBJETIVO: Dar "Vida" e movimento ao nosso App Frontend. É aqui onde o 
 *   Navegador conversa de verdade com a Inteligência Artificial e obedece
 *   comandos de clique!
 * ========================================================================== */

// Este evento funciona como um aviso: "Só inicie este Javascript quando TODO o HTML da tela estiver desenhado!"
document.addEventListener('DOMContentLoaded', () => {

    // -------------------- PEGAR ELEMENTOS DO HTML (CAPTURAS) --------------------
    // Aqui damos um "apelido" no javascript para as partes do nosso design no HTML
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const sendButton = document.getElementById('send-button');
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const sidebar = document.querySelector('.sidebar');

    // -------------------- LÓGICA DE DIMENSIONAMENTO DO TEXTAREA --------------------
    // Quando o usuário está digitando (evento 'input'), a caixa de texto vai crescendo de tamanho auto
    messageInput.addEventListener('input', function () {
        this.style.height = 'auto'; // Zera o tamanho base
        this.style.height = (this.scrollHeight) + 'px'; // Estica ela de acordo com a altura interna da barra de rolamento invisível.

        // Se a caixa estiver fazia apenas com espaços ('trim'), desabilita o botão avião de envio!
        if (this.value.trim() === '') {
            sendButton.disabled = true;
        } else {
            sendButton.disabled = false;
        }
    });

    // -------------------- LÓGICA DO BOTÃO ENTER (TECLADO) --------------------
    messageInput.addEventListener('keydown', function (e) {
        // Se a tecla for ENTER E a tecla SHIFT NÃO estiver sendo pressionada (Shift+Enter é pular linha normalmente)...
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Impede o Enter de pular linha do input e bagunçar a caixa

            const messageText = this.value.trim();
            // Só executo o envio se não estiver com o input vazio
            if (messageText !== '') {
                sendMessage(messageText); // MANDA PARA A INTELIGÊNCIA!
            }
        }
    });

    // -------------------- MENU EM DISPOSITIVO MÓVEL --------------------
    // Se o botão Hambúrguer existe na tela (Apenas quando diminui pra tamanho celular CSS)
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            // A classe 'Toggle' alterna ligado/desligado o 'open'. Trazendo o "painel" pra tela!
            sidebar.classList.toggle('open');
        });
    }

    // -------------------- CLICAR NO 'AVIÃO DE PAPEL' DO HTML --------------------
    // Quando aperta Send/Submit:
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Pára a tela de dar REFRESH/F5 na página de forma nativa e estressante!
        const messageText = messageInput.value.trim();
        if (messageText !== '') {
            sendMessage(messageText);
        }
    });

    // ==============================================================================
    // A FUNÇÃO PRINCIPAL: ENVIO ASSÍNCRONO DA MENSAGEM ("async")
    // async / await faz o navegador pausar silenciosamente enquanto o Python e a IA respondem
    // ==============================================================================
    async function sendMessage(messageText) {
        // 1. Apaga tudo que tá digitado porque a gente já pegou o texto.
        messageInput.value = '';
        messageInput.style.height = 'auto'; // Recua tamanho nativo da textarea
        sendButton.disabled = true;

        // 2. Coloca o balão azul de "Humano fala" na tela, na mesma hora que ele clicou
        appendMessage('user', messageText);

        // 3. Coloca os 3 pontinhos simulando a "IA Digitando..." para o usuário não achar q travou
        const typingId = showTypingIndicator();

        try {
            // 4. MANDA UMA REQUISIÇÃO (FETCH) PELA INTERNET PRO NOSSO PYTHON FASTAPI (app.py) !!!!
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText }) // Converte nosso texto num JSON para o Pythoon ler!
            });

            // 5. PYTHON finalizou de ler a IA Groq! Tira a bolinha pulando!
            removeTypingIndicator(typingId);

            // Algum erro HTTP (500, 404, etc)
            if (!response.ok) {
                appendMessage('agent', 'Ocorreu um erro ao processar sua solicitação.');
                return;
            }

            // Descarta a fita envolvente e puxa o JSON bruto
            const data = await response.json();

            // 6. Coloca o balão de resposta verde com texto que Groq Llama enviou (E ativa marcação Negrito Markdown)
            if (data.response) {
                appendMessage('agent', data.response, true);
            }

            // 7. SURPRESA NO ZABBIX: Alguma ferramenta crítica interceptou! O Backend Python nos alertou
            if (data.confirmations && data.confirmations.length > 0) {
                data.confirmations.forEach(conf => {
                    appendConfirmationBox(conf); // GERA A CAIXA "APROVAR/REJEITAR" no texto vermelho!
                });
            }

        } catch (error) {
            // Se caiu o backend ou sem internet
            console.error("Error:", error);
            removeTypingIndicator(typingId);
            appendMessage('agent', 'Falha na comunicação com o servidor. Verifique o console ou conexão.');
        }
    }

    // ==============================================================================
    // FUNÇÕES COMPONENTES (CRIANDO BURACOS DOM HTML DINAMICAMENTE)
    // ==============================================================================

    // Construtor Visual do Balãozinho
    function appendMessage(sender, text, isMarkdown = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        // Cria icone de robo ou de homenzinho
        avatarDiv.innerHTML = sender === 'agent' ? '<i class="fa-solid fa-robot"></i>' : '<i class="fa-solid fa-user"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // O Agente Noc responde em Markdown, então se for ele a gente 'Parseia' tabelinhas.
        if (isMarkdown && sender === 'agent') {
            contentDiv.innerHTML = marked.parse(text);
        } else {
            const p = document.createElement('p');
            p.textContent = text;
            contentDiv.appendChild(p);
        }

        // Gruda os pedaços uns nos outros
        msgDiv.appendChild(avatarDiv);
        msgDiv.appendChild(contentDiv);

        // Chumba no HTML da tela grandão!
        chatMessages.appendChild(msgDiv);

        // Empurra o scroll do mouse lá pra baixo automático!
        scrollToBottom();
    }

    // Caixa que aparece vermelhar para aprovar operação zabbix
    function appendConfirmationBox(confData) {
        // Ele vai espetar essa caixinha DENTRO no último balao verde (Agente Noc)!
        const lastAgentMessage = chatMessages.querySelectorAll('.agent-message .message-content');
        if (lastAgentMessage.length === 0) return;
        const targetContainer = lastAgentMessage[lastAgentMessage.length - 1];

        const box = document.createElement('div');
        box.className = 'confirmation-box';
        box.id = `conf-${confData.correlation_id}`;

        // Código que cria o visual brutal com os botões verdes e vermelhos
        box.innerHTML = `
            <p><i class="fa-solid fa-triangle-exclamation"></i> Ação Requer Aprovação</p>
            <p>${confData.message}</p>
            <div class="confirm-actions">
                <button class="btn-confirm" onclick="handleConfirm('${confData.correlation_id}', '${confData.action}', '${encodeURIComponent(JSON.stringify(confData.data))}')"><i class="fa-solid fa-check"></i> Aprovar</button>
                <button class="btn-reject" onclick="handleReject('${confData.correlation_id}')"><i class="fa-solid fa-xmark"></i> Rejeitar</button>
            </div>
        `;

        targetContainer.appendChild(box);
        scrollToBottom();
    }

    // Quando clica no Botão de Aprovação
    // window. indica que a função é liberada generalizada pelo navegador inteiro fora deste evento isolado domcontentloaded.
    window.handleConfirm = async function (correlationId, action, dataStr) {
        const box = document.getElementById(`conf-${correlationId}`);
        // Troca o Botão verde momentâneo por bolinha girando "Executando Ação..." e corta a função
        box.innerHTML = `<p><i class="fa-solid fa-spinner fa-spin"></i> Executando ação...</p>`;

        try {
            const data = JSON.parse(decodeURIComponent(dataStr)); // Retrai os dados crus

            // Re-acelera contra o Python, desta vez batendo não na rola '/chat', e sim em '/confirm' 
            const response = await fetch('/api/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ correlation_id: correlationId, action: action, data: data })
            });

            const result = await response.json();

            // SE a ação do Zabbix ocorreu com sucesso puro, mostra 'Mensagem Vitória Verde'  ✓
            if (response.ok) {
                box.innerHTML = `<p style="color: var(--accent);"><i class="fa-solid fa-check-circle"></i> ${result.message}</p>`;
            } else {
                // SE por um exemplo, a conexão do zabbix quebrou Timeout 'Mensagem vermelha errônea'
                box.innerHTML = `<p style="color: var(--danger);"><i class="fa-solid fa-circle-xmark"></i> Erro: ${result.error}</p>`;
            }
        } catch (err) {
            box.innerHTML = `<p style="color: var(--danger);"><i class="fa-solid fa-circle-xmark"></i> Erro de rede ao confirmar.</p>`;
        }
    };

    // Botão de Rejeitar Abortar
    window.handleReject = function (correlationId) {
        const box = document.getElementById(`conf-${correlationId}`);
        // Altera para Cinza
        box.innerHTML = `<p style="color: var(--text-muted);"><i class="fa-solid fa-ban"></i> Ação cancelada pelo operador.</p>`;
    };

    // FUNÇÕES DE LIMPEZA E SUPORTE VISUAL (Não mexa)
    // -----------------------------------------------------
    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = `message agent-message`;
        msgDiv.id = id;

        msgDiv.innerHTML = `
            <div class="message-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
        return id; // Retorna um crachá de ID para destruir essa caixa depois
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove(); // Destrói os três pulinhos
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight; // Desliza pra baixo
    }

    // Auto-disable base logo de cara
    sendButton.disabled = true;
});
