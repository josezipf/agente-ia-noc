import os
import json
import ipaddress
import re
import requests
import subprocess
import platform
from dotenv import load_dotenv
from pyzabbix import ZabbixAPI

load_dotenv()

# =====================================================================
# GERENCIAMENTO DE ESTADO DA CONEXÃO (SINGLETON)
# =====================================================================
# Variável global privada para guardar a sessão viva na memória
_zapi_instance = None

def get_zabbix_connection() -> ZabbixAPI:
    """
    Retorna a conexão com o Zabbix. Se não existir, cria uma nova.
    Isso evita múltiplos logins (overhead) a cada chamada da IA.
    """
    global _zapi_instance
    
    # Se a conexão já foi criada antes, apenas devolve ela (Reutilização)
    if _zapi_instance is not None:
        return _zapi_instance
        
    # Se for a primeira vez rodando, faz o login
    zabbix_url = os.getenv("ZABBIX_URL")
    zabbix_token = os.getenv("ZABBIX_TOKEN")
    
    _zapi_instance = ZabbixAPI(server=zabbix_url)
    _zapi_instance.timeout = 5 
    _zapi_instance.login(api_token=zabbix_token)
    
    return _zapi_instance

# =====================================================================
# FUNÇÕES DE NEGÓCIO E TOOLS
# =====================================================================
def validar_host_existe_api(zapi: ZabbixAPI, nome_host: str) -> bool:
    hosts_encontrados = zapi.host.get(filter={"host": nome_host})
    return len(hosts_encontrados) > 0

def preparar_cadastro_host(nome_host: str, ip: str) -> str:
    """
    Prepara os dados para cadastrar um novo host no Zabbix.
    
    REGRAS OBRIGATÓRIAS PARA USO DESTA FERRAMENTA:
    1. Só chame esta ferramenta se o usuário explicitamente pedir para criar/cadastrar um host.
    2. Você PRECISA de um IP no formato numérico (ex: 192.168.0.10).
    3. NUNCA invente, deduza ou adivinhe um IP. Se o usuário falar "o mesmo IP", NÃO CHAME A FERRAMENTA. Pergunte o IP exato.
    """
    if not re.match(r"^[a-zA-Z0-9_-]+$", nome_host):
        return json.dumps({
            "status": "error",
            "message": f"O nome '{nome_host}' contém caracteres inválidos. Use apenas letras, números, hifens ou underlines."
        })

    try:
        ipaddress.IPv4Address(ip)
    except ipaddress.AddressValueError:
        return json.dumps({
            "status": "error",
            "message": f"O IP '{ip}' é inválido. Informe o operador."
        })

    try:
        # Agora usamos a função inteligente que reutiliza a conexão!
        zapi = get_zabbix_connection()
        
        if validar_host_existe_api(zapi, nome_host):
            return json.dumps({
                "status": "error",
                "message": f"Já existe um host com o nome '{nome_host}' no Zabbix. Aborte a ação."
            })
        
        return json.dumps({
            "status": "pending",
            "action": "create_host",
            "target_system": "zabbix",
            "data": {
                "nome_host": nome_host,
                "ip": ip
            }
        })
    except requests.exceptions.Timeout:
         return json.dumps({"status": "error", "message": "O servidor Zabbix demorou muito para responder (Timeout)."})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Falha de comunicação: {str(e)}"})

def executar_criacao_real(dados: dict) -> dict:
    try:
        # Aqui também usamos a conexão reutilizável. Zero logins desnecessários!
        zapi = get_zabbix_connection()
        
        host_criado = zapi.host.create(
            host=dados["nome_host"],
            status=0,
            interfaces=[{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": dados["ip"],
                "dns": "",
                "port": "10050"
            }],
            groups=[{"groupid": "2"}],

            # ADICIONANDO O TEMPLATE PADRÃO LINUX AQUI 👇
            templates=[{"templateid": "10001"}]
        )
        id_novo_host = host_criado['hostids'][0]
        
        return {
            "status": "success",
            "host_id": id_novo_host,
            "message": f"✅ Host '{dados['nome_host']}' provisionado com sucesso (ID: {id_novo_host})."
        }
    except requests.exceptions.Timeout:
         return {"status": "error", "message": "❌ Timeout na execução. O Zabbix não respondeu a tempo."}
    except Exception as e:
        return {"status": "error", "message": f"❌ Erro crítico ao gravar no Zabbix: {str(e)}"}

def executar_ping(ip_ou_host: str) -> str:
    """
    Executa um comando de Ping no sistema operacional para testar a conectividade de rede.
    Use esta ferramenta quando o usuário reclamar que um host está fora ou não responde,
    ANTES de criar alarmes ou se o usuário explicitamente pedir um ping.
    
    Args:
        ip_ou_host (str): O endereço IP ou nome (FQDN) do host a ser pingado.
    """
    try:
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        comando = ['ping', param, '4', ip_ou_host]
        resultado = subprocess.run(comando, capture_output=True, text=True, timeout=10)
        
        if resultado.returncode == 0:
            return json.dumps({
                "status": "success",
                "message": f"Ping para {ip_ou_host} bem sucedido.",
                "output": resultado.stdout
            })
        else:
            return json.dumps({
                "status": "warning",
                "message": f"Ping para {ip_ou_host} falhou. O host pode estar inoperante ou bloqueando ICMP.",
                "output": resultado.stdout or resultado.stderr
            })
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "error", "message": f"O ping para {ip_ou_host} excedeu o tempo limite."})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Erro ao tentar executar ping: {str(e)}"})

def consultar_status_host(nome_host: str) -> str:
    """
    Consulta a API do Zabbix para verificar se um host existe, se está monitorado (ativo)
    e se possui alguma trigger (alarme) problemática ativa no momento.
    
    Args:
        nome_host (str): O nome exato do host no Zabbix.
    """
    try:
        zapi = get_zabbix_connection()
        
        hosts = zapi.host.get(
            filter={"host": nome_host},
            output=["hostid", "host", "status", "available", "error"],
            selectInterfaces=["ip"]
        )
        
        if not hosts:
            return json.dumps({
                "status": "not_found",
                "message": f"Nenhum host com o nome '{nome_host}' foi encontrado no Zabbix."
            })
            
        host = hosts[0]
        host_id = host["hostid"]
        status_monitoramento = "Ativo" if host["status"] == "0" else "Desativado"
        
        # Buscar triggers em estado de problema para esse host
        problemas = zapi.trigger.get(
            hostids=host_id,
            only_true=1,
            skipDependent=1,
            monitored=1,
            active=1,
            output=["description", "priority", "lastchange"]
        )
        
        lista_problemas = []
        for p in problemas:
            lista_problemas.append({
                "descricao": p["description"],
                "prioridade": p["priority"]
            })
            
        return json.dumps({
            "status": "success",
            "host": host["host"],
            "ip": host["interfaces"][0]["ip"] if host.get("interfaces") else "N/A",
            "monitoramento": status_monitoramento,
            "agente_disponivel": host["available"],
            "erro_agente": host["error"],
            "total_problemas": len(lista_problemas),
            "problemas": lista_problemas
        })
        
    except requests.exceptions.Timeout:
         return json.dumps({"status": "error", "message": "O servidor Zabbix demorou muito para responder (Timeout)."})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Falha ao consultar Zabbix: {str(e)}"})