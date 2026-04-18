# 🌐 Projeto NOC AI Agent - AIOps Dashboard

Bem-vindo ao **NOC AI Agent Web**, um laboratório avançado e didático que mescla Inteligência Artificial generativa com automação de operação de redes (NOC) utilizando o Zabbix!

Este projeto foi construído step-by-step para propósitos de estudos onde conectamos um modelo de Linguagem Larga (Large Language Model - Llama 3 via Groq) num backend robusto com interatividade moderna num navegador HTML.

---

## 🎯 O Que Este Projeto Faz?

Ele providencia um "Console Operacional Inteligente".
Em vez de você entrar no dashboard do Zabbix, navegar em múltiplos formulários, e digitar informações na mão, você conversa com a Inteligência Artificial.

> **Exemplo Prático**:
> *"Cadastre meu novo roteador Core no IP 10.0.0.2 com o nome de RO-CORE-02"*
> A IA processa, entende, chama as ferramentas nos bastidores, checa se o host já existe e, após validação, pergunta no navegador: **"Posso autorizar no Zabbix?"**. Ao aprovar, o script interage automaticamente na API do Zabbix! Zero atrito humano além da autorização.

## 🛠 Arquitetura do Software

Este projeto abandonou a interface via terminal (CLI) clássica para proporcionar uma arquitetura web real e responsiva separando Frontend e Backend:

### 1. **Data e Lógica (Python & Agno / Backend)**
*   `agente_noc.py`: Define o perfil da IA. Quem ela é, que ferramentas tem, e suas travas lógicas contra alucinações de dados falsos (Instruções customizadas).
*   `zabbix_tools.py`: Possui as lógicas de conexão com a infraestrutura Zabbix e as ações puras. (É o braço atuador).
*   `app.py`: O "maestro" utilizando **FastAPI**. Cria a ponte (Endpoint `/api/chat`) para ouvir os comandos do site e devolver a fala da Inteligência juntamente de notificações que requisitem aprovação humana no Front.

### 2. **Interface Visual (HTML/CSS/JS / Frontend)**
*   `static/index.html`: A Estrutura esquelética. Um design com caixas, um menu lateral, botões e caixas de textos.
*   `static/style.css`: Providencia as animações, cores vibrantes corporativas, tema noturno (_Dark Mode_) e a textura moderna _Glassmorphism_ (Translúcido).
*   `static/script.js`: O comportamento dinâmico e cérebro do Frontend. Escuta seus cliques de 'Enviar' e despacha os pacotes para o `app.py`, desenhando os balões de conversa e botões de confirmação instantaneamente sem a necessidade de recarregar a visualização, criando experiência "Live Chat".

---

## 👨‍💻 Como utilizar? (Instruções para Alunos e Estudantes)

Você pode explorar todo o código destrinchando arquivo por arquivo. **Tudo está profundamente comentado passo-a-passo e linha-a-linha.**

**Para colocar "de pé" o servidor**:

1. Crie seu arquivo base caso ainda não exista:
   Crie um `.env` com os Tokens da LLM. (Exemplo `GROQ_API_KEY` e senhas do `ZABBIX_API`).
2. Ative seu Ambiente Virtual:
   ```bash
   source .venv/bin/activate
   ```
3. Garanta a Instalação das bibliotecas web
   ```bash
   pip install fastapi uvicorn requests pyzabbix "agno>=0.2"
   ```
4. Excute a sua API e deixe a mágica acontecer:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

Tudo vai iniciar localmente e você pode monitorar pela aba Web navegando para **http://localhost:8000**.

> **Aviso de Aprimoramento**: Os Códigos já são responsivos (Cabem nas telas de celular limitadas)! Tente acessar com a ferramenta F12 ou enviar do celular.

---
**Elaborado Por:** Agente Antigravity com base nos direcionamentos de desenvolvimento e melhores padrões de infraestrutura (TI)!
