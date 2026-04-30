import os
import json
import logging
import uuid
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.groq import Groq
from agno.db.sqlite import SqliteDb

# Importamos do nosso arquivo de ferramentas
from zabbix_tools import preparar_cadastro_host, executar_criacao_real

load_dotenv()

# Configuração de Logs Estruturados para Auditoria
logging.basicConfig(level=logging.INFO, format='%(message)s')

if not os.getenv("GROQ_API_KEY"):
    print("Erro: GROQ_API_KEY não encontrada no arquivo .env")
    exit(1)

# Instruções blindadas para evitar confusão do LLM
instrucoes = (
    "Você é um Assistente Especialista em NOC e Zabbix. "
    "Sua missão é ajudar os operadores de rede com eficiência. "
    "Para criar ou cadastrar hosts, utilize EXCLUSIVAMENTE a ferramenta 'preparar_cadastro_host'. "
    "COMO TRATAR O RETORNO DA FERRAMENTA: "
    "- Se a ferramenta retornar um JSON com status 'error', explique o motivo do erro para o usuário de forma clara. "
    "- Se a ferramenta retornar um JSON com status 'pending', diga APENAS: 'Dados validados! O sistema aguarda sua autorização no terminal para o provisionamento.' "
    "REGRAS ANTES DE CHAMAR A FERRAMENTA: "
    "1. Nunca invente IPs. "
    "2. Se o usuário esquecer o IP ou pedir 'o mesmo IP', NÃO CHAME a ferramenta. Apenas pergunte qual é o IP exato."
)

# Configuração do Agente
agente_noc = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    description="Especialista em NOC",
    instructions=instrucoes,
    tools=[preparar_cadastro_host], 
    db=SqliteDb(session_table="agent_sessions", db_file="agente_noc_memoria.db"),
    add_history_to_context=True,
    debug_mode=True,       
    markdown=True          
)

def iniciar_chat_cli():
    print("="*70)
    print("🤖 Plataforma AIOps - Console NOC (Controller)")
    print("="*70)
    
    while True:
        try:
            pergunta = input("\n[Operador] ❯ ")
            if pergunta.strip().lower() in ['sair', 'exit']:
                print("\n[Agente] Encerrando o console. Bom plantão!")
                break
            if not pergunta.strip():
                continue
            
            # 1. A IA GERA A RESPOSTA
            resposta = agente_noc.run(pergunta)
            
            # 2. IMPRIME A MENSAGEM DA IA
            print(f"\n[Agente]\n{resposta.content}")
            
            # 3. O CONTROLLER ENTRA EM AÇÃO
            # O sistema Agno oculta a tool na resposta final. Temos que caçar no histórico recente as tools acionadas.
            if hasattr(resposta, 'messages') and isinstance(resposta.messages, list):
                for msg in reversed(resposta.messages):
                    if getattr(msg, "role", "") == "user":
                        break # Chegamos na pergunta principal do usuário, paramos a busca p/ não pegar resíduo antigo
                        
                    if getattr(msg, "role", "") == "tool" and getattr(msg, "content", ""):
                        try:
                            # Converte o conteúdo bruto para verificar se é o JSON das nossas tools
                            resultado_str = str(msg.content)
                            if not resultado_str.strip().startswith("{"):
                                continue

                            resultado_tool = json.loads(resultado_str)
                            
                            # Se for erro de IP inválido ou host existente ignoramos
                            if resultado_tool.get("status") == "error":
                                continue
                            
                            # ROTEAMENTO: Analisa se a ação é de criar host no Zabbix
                            if resultado_tool.get("status") == "pending" and resultado_tool.get("action") == "create_host":
                                dados_host = resultado_tool["data"]
                                
                                # Rastreabilidade: Geramos um ID único para essa operação
                                correlation_id = str(uuid.uuid4())
                                
                                # LOG de Intenção
                                logging.info(json.dumps({
                                    "correlation_id": correlation_id,
                                    "event": "host_creation_requested",
                                    "host": dados_host["nome_host"],
                                    "ip": dados_host["ip"],
                                    "operator": "cli_user"
                                }))
                                
                                # INTERAÇÃO HUMANA (Segurança Crítica)
                                print("\n" + "="*50)
                                print(f"[CONTROLLER] ⚠️ AÇÃO CRÍTICA INTERCEPTADA (Ticket: {correlation_id[:8]})")
                                print(f"Confirmar criação do host: {dados_host['nome_host']} ({dados_host['ip']})?")
                                confirm = input("Digite 's' para aprovar ou 'n' para rejeitar ❯ ")
                                print("="*50)
                                
                                if confirm.lower() == 's':
                                    print("\n[CONTROLLER] Executando provisionamento...")
                                    
                                    # Executa a ação real na infraestrutura
                                    resultado_exec = executar_criacao_real(dados_host)
                                    print(f"[CONTROLLER] {resultado_exec['message']}")
                                    
                                    # LOG de Resultado Final
                                    logging.info(json.dumps({
                                        "correlation_id": correlation_id,
                                        "event": "host_creation_executed",
                                        "host": dados_host["nome_host"],
                                        "status": resultado_exec["status"]
                                    }))
                                else:
                                    print("\n[CONTROLLER] Ação abortada pelo operador.")
                                    # LOG de Aborto
                                    logging.info(json.dumps({
                                        "correlation_id": correlation_id,
                                        "event": "host_creation_aborted",
                                        "host": dados_host["nome_host"]
                                    }))
                        except Exception as json_err:
                            pass

        except (KeyboardInterrupt, EOFError):
            print("\n\n[Agente] Operação interrompida pelo usuário.")
            break
        except Exception as e:
            print(f"\n[Erro no Controller]: {e}")

if __name__ == "__main__":
    iniciar_chat_cli()