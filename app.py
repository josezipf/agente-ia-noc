# ==============================================================================
# ARQUIVO: app.py
# OBJETIVO: Servir como o "Coração" (Backend) da nossa aplicação Web.
# 
# O QUE ESTE CÓDIGO FAZ?
# 1. Ele cria um servidor web usando um framework chamado "FastAPI".
# 2. Hospeda nossa pasta "static", onde ficam nossos visuais (HTML, CSS, JS).
# 3. Cria "Endpoints" (caminhos de API como '/api/chat') para onde o 
#    navegador pode enviar e pedir informações.
# 4. Conecta o "Chat HTML" do navegador com a "Inteligência" (agente_noc.py).
# ==============================================================================

# ----------------- IMPORTAÇÕES (TRAZENDO FERRAMENTAS) -------------------------
# Importa o FastAPI, Request (para ver o que o usuário mandou)
from fastapi import FastAPI, Request
# Importa formatos de resposta para o navegador: 
# HTMLResponse para mandar páginas da web, e JSONResponse para mandar dados.
from fastapi.responses import HTMLResponse, JSONResponse
# Permite ao FastAPI ler pastas onde guardamos fotos, CSS e JavaScript
from fastapi.staticfiles import StaticFiles
# Pydantic é usado no FastAPI para validar se o dado do usuário veio no formato certo
from pydantic import BaseModel
# Bibliotecas nativas do Python: json para lidar com textos estruturados, 
# logging para histórico/auditoria e uuid para criar IDs únicos
import json
import logging
import uuid
import os

# Importamos nosso Agente Inteligente do nosso outro arquivo 
from agente_noc import agente_noc
# Importamos a nossa ferramenta que realmente cadastra o host no Zabbix
from zabbix_tools import executar_criacao_real

# ---------------- CONFIGURAÇÃO DO SERVIDOR ------------------------------------
# Criamos a "Aplicação Web" e damos um título a ela.
app = FastAPI(title="NOC AI Agent Web Interface")

# Dizemos para o FastAPI: "Tudo que estiver na pasta /static está liberado para o navegador acessar"
# É graças a isso que o navegador consegue baixar o style.css e o script.js.
app.mount("/static", StaticFiles(directory="static"), name="static")

# ----------------- MODELOS DE DADOS (VALIDAÇÃO) -------------------------------
# Criamos uma regra: Quando um usuário mandar mensagem, DEVE ter um campo "message" que é string (texto)
class ChatRequest(BaseModel):
    message: str

# Criamos uma regra: Se o usuário clica em "APROVAR", precisa mandar o ID da operação, a ação e os dados
class ConfirmRequest(BaseModel):
    correlation_id: str  # ID único para rastrear no Log
    action: str          # Ação a ser feita (ex: "create_host")
    data: dict           # Dicionário com informações (como IP e Nome do host)

# ----------------- ROTAS DO SISTEMA (ENDPOINTS) -------------------------------

# ROTA 1: A Rota Raiz ('/') 
# Quando o usuário digitar "localhost:8000" no navegador, esta função será ativada.
@app.get("/")
async def read_root():
    # Abre o arquivo 'index.html' que é o esqueleto da nossa página
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    # Envolve o código HTML encontrado num "envelope" e envia para quem pediu
    return HTMLResponse(content=html_content)

# ROTA 2: endpoint de CHAT ('/api/chat')
# Esta rota não abre uma página visual. Ela funciona nos bastidores. O script.js chama ela!
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    # Cortamos os espaços em branco para garantir que o usuário não mandou só espaços
    if not request.message.strip():
        # Retorna Erro 400 (Bad Request) avisando que está vazio
        return JSONResponse(status_code=400, content={"error": "Mensagem vazia."})
        
    pergunta = request.message
    try:
        # AQUI A MAGIA ACONTECE: Pegamos a pergunta e enviamos para a IA.
        # .run(pergunta) envia e aguarda ela responder (usando a Groq e o LLama 3)
        resposta = agente_noc.run(pergunta)
        
        # Pega a "fala" escrita da resposta. Se bugar, transforma pra string simples.
        texto_resposta = resposta.content if hasattr(resposta, "content") else str(resposta)
        
        # PARTE DO CONTROLLER (SEGURANÇA):
        # A inteligência tentou chamar ferramentas por trás dos panos?
        tools_chamadas = resposta.tools if hasattr(resposta, 'tools') and resposta.tools is not None else []
        
        confirmations_needed = [] # Lista das aprovações que vamos cobrar do usuário visualmente!
        
        # Para cada ferramenta que a IA queria executar...
        for tool in tools_chamadas:
            try:
                # Tenta transformar o resultado que a ferramenta gerou em um dicionário (JSON)
                resultado_tool = json.loads(tool.result) if hasattr(tool, 'result') and tool.result else {}
                
                # Se for erro, apenas ignoramos para que a IA fale do erro ela mesma ("IP inválido", etc)
                if resultado_tool.get("status") == "error":
                    continue
                
                # SE a IA chamou a ferramenta e ela devolveu que a ação real precisa ser aprovada (create_host do Zabbix)...
                if resultado_tool.get("action") == "create_host" and resultado_tool.get("target_system") == "zabbix":
                    dados_host = resultado_tool["data"]
                    
                    # RASTREABILIDADE - Geramos um protocolo único aleatório de 32 letras para LOG e Botão Confirmar
                    correlation_id = str(uuid.uuid4())
                    
                    # LOG DE AUDITORIA: "O usuário X tentou criar um Host Y"
                    logging.info(json.dumps({
                        "correlation_id": correlation_id,
                        "event": "host_creation_requested_web",
                        "host": dados_host["nome_host"],
                        "ip": dados_host["ip"],
                        "operator": "web_user"
                    }))
                    
                    # Nós então preenchemos o aviso que aparecerá APÓS a fala da IA, pedindo pra ela apertar o botão Aprovar.
                    confirmations_needed.append({
                        "correlation_id": correlation_id,
                        "action": "create_host",
                        "data": dados_host,
                        "message": f"Confirmar criação do host: {dados_host['nome_host']} ({dados_host['ip']})?"
                    })
                    
            except Exception as ex:
                logging.error(f"Erro ao parsear chamada de tool: {ex}")
                pass
                
        # Empacota a (Resposta Falada + Botões de Confirmação Pendentes) e Devolve para o Javascript!
        return JSONResponse(content={
            "response": texto_resposta,
            "confirmations": confirmations_needed
        })

    except Exception as e:
        # Se TUDO der errado (IA fora do ar, bug feio), avolume 500 (Erro Interno no Servidor) e avise
        return JSONResponse(status_code=500, content={"error": str(e)})

# ROTA 3: Rota de Confirmação ('/api/confirm')
# Quando o usuário CLICA NO BOTÃO "APROVAR", é disparado um alerta para esta rota!
@app.post("/api/confirm")
async def confirm_action(request: ConfirmRequest):
    try:
        # Se a ação recebida foi realmente pra criar o host
        if request.action == "create_host":
            dados_host = request.data
            
            # AGORA SIM É PRA VALER! 
            # Chama a função python que realmente entra no Zabbix e altera a infraestrutura
            resultado_exec = executar_criacao_real(dados_host)
            
            # LOG DE AUDITORIA de término: "O host Y foi ou não efetivado"
            logging.info(json.dumps({
                "correlation_id": request.correlation_id,
                "event": "host_creation_executed_web",
                "host": dados_host.get("nome_host", "unknown"),
                "status": resultado_exec["status"]
            }))
            
            # Responde para a tela com a mensagem vitoriosa ou o erro do Zabbix ( Timeout, etc )
            return JSONResponse(content={"message": resultado_exec["message"], "status": resultado_exec["status"]})
        else:
            return JSONResponse(status_code=400, content={"error": "Ação desconhecida."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# Bloco final que põe o servidor de pé na porta 8000
if __name__ == "__main__":
    import uvicorn
    # reload=True ajuda quando você altera o arquivo Py, ele atualiza automaticamente
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
