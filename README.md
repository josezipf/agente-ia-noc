# 🤖 Agente NOC & Zabbix - AIOps

Bem-vindo ao repositório do **Agente NOC AI**, um assistente de infraestrutura de TI conversacional desenvolvido de ponta a ponta para auxiliar operadores de rede e SysAdmins nas tarefas diárias!

Este projeto integra o incrível poder dos grandes modelos de linguagem (via **Groq / Llama 3**) com automações ativas de rede utilizando o **Zabbix API**, fornecendo tanto uma interface Web interativa (via FastAPI) quanto uma Interface por Linha de Comando (CLI Controller).

## 🎯 Objetivos Educacionais
Este projeto foi desenvolvido com forte viés didático para o estudo prático de:
- **AIOps (Artificial Intelligence for IT Operations):** Integrando IAs com infraestrutura real.
- **Agentic AI:** Uso do framework `Agno` com ferramentas ativas (tools) de automação.
- **Human-in-the-Loop:** Controller de segurança que bloqueia e audita ações destrutivas ou de criação de TI (como provisionamento de Hosts) antes do LLM executá-las.
- **FastAPI Moderno:** Construção limpa de endpoints assíncronos e páginas Web estáticas.

## ⚙️ Funcionalidades
- [x] Consulta conversacional com IA especialista em Redes.
- [x] Integração direta e transparente com Zabbix (Criação de Hosts, Configurações).
- [x] Interface Web com "Glassmorphism" design e histórico de chat.
- [x] CLI Terminal interativo focado para Sysadmins (`agente_noc.py`).
- [x] Log Auditável (rastreabilidade via UUID em todas as ações).

---

## 🚀 Como instalar e rodar (Para Alunos)

### 1. Clonando o Repositório
Abra o seu terminal e faça o clone deste repositório:
```bash
git clone https://github.com/josezipf/agente-ia-noc.git
cd agente-ia-noc
```

### 2. Configurando o Ambiente Virtual Python (Recomendado)
```bash
python -m venv .venv
source .venv/bin/activate  # Se estiver no Windows: .venv\Scripts\activate
```

### 3. Instalando as Dependências
O projeto utiliza algumas das bibliotecas de IA e backend mais modernas:
```bash
pip install fastapi uvicorn pydantic agno groq python-dotenv pyzabbix requests
```

### 4. Configurando as Senhas de Acesso (Crucial!)
A lógica de autenticação da IA (Groq) e do monitoramento (Zabbix) usa arquivos ocultos chamados `.env`. O próprio GitHub **não** salva o meu `.env` original por segurança.
Você deve criar o seu:

1. Modifique ou duplique o arquivo `.env.example` renomeando-o para `.env`.
2. Abra o arquivo `.env` gerado e insira a SUA chave de API da Groq e o endereço do Zabbix do seu escopo:
   ```env
   GROQ_API_KEY=sua_chave_groq_aqui
   ZABBIX_URL=http://SEU_IP/zabbix
   ZABBIX_TOKEN=seu_token_api_aqui
   ```

### 5. Executando o Projeto

Você tem duas formas de executar a aplicação:

**Opção A) Apenas Terminal (Raiz DevOps/SysAdmin)**
```bash
python agente_noc.py
```

**Opção B) Interface Gráfica / Dashboard Web (Controller de AIOps)**
```bash
python app.py
```
*Após rodar o comando acima, basta abrir o seu navegador no endereço: [http://localhost:8000](http://localhost:8000).*

---

### 🛡️ Disclaimer de Segurança
Neste repositório de estudos, **NENHUM DADO SENSÍVEL VAZA**. Graças à abordagem com arquivo `.gitignore` isolando as credenciais e ambientes, todos os clones saem com segurança máxima. Lembre-se, LLM "Tools" são ações interativas—utilize sempre o mecanismo de aprovação (Human-In-The-Loop) previsto no código!
