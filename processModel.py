import os

def processosTodos():
    """Retorna e imprime uma lista de todos os PIDs encontrados em /proc"""
    processosID = [processosID for processosID in os.listdir('/proc') if processosID.isdigit()] #lista os processos do diretorio proc, verifica se todos os processos são dígitos.
    print("processosID encontrados:", processosID)
    return processosID


import pwd

def statusProcesso(processosID):
    """Lê e retorna os dados do arquivo /proc/[pid]/status como dicionário"""

    status_path = f'/proc/{processosID}/status'
    status_info = {}

    print(f"\n Lendo arquivo: {status_path}")
    try:
        with open(status_path, 'r') as f:
            for linha in f:
                if linha.startswith("Name:"):
                    status_info["nome"] = linha.split()[1]
                elif linha.startswith("State:"):
                    status_info["estado"] = " ".join(linha.split()[1:])
                elif linha.startswith("Uid:"):
                    uid = int(linha.split()[1]) #seleciona o Usuário Id real, segundo elemento da linha
                    status_info["usuario"] = pwd.getpwuid(uid).pw_name #Acessa o banco de dados e pega o Usuario Id correspondente e seleciona o nome desse usuário
                elif linha.startswith("Threads:"):
                    status_info["threads"] = int(linha.split()[1])
                elif linha.startswith("VmSize:"):
                    status_info["mem_total_kb"] = int(linha.split()[1])
                elif linha.startswith("VmRSS:"):
                    status_info["mem_residente_kb"] = int(linha.split()[1])
                elif linha.startswith("VmData:"):
                    status_info["mem_heap_kb"] = int(linha.split()[1])
                elif linha.startswith("VmStk:"):
                    status_info["mem_stack_kb"] = int(linha.split()[1])
                elif linha.startswith("VmExe:"):
                    status_info["mem_codigo_kb"] = int(linha.split()[1])
    except FileNotFoundError:
        print(f"Processo {processosID} não existe ou terminou.")
        return None
    except PermissionError:
        print(f"Sem permissão para acessar {status_path} (PermissionError)")
        return None

    return status_info

def dicionarioStatusProcesso():
    """Retorna um dicionário com os status de todos os processos ativos"""
    processos_info = {}
    for processosID in processosTodos():
        info = statusProcesso(processosID)
        if info:  # Ignora processos que não puderam ser lidos
            processos_info[processosID] = info
    return processos_info

def cpuProcesso(processosID):
    """Lê e retorna os dados do arquivo /proc/[pid]/stat como dicionário"""
    stat_path = f'/proc/{processosID}/stat'
    print(f"\n Lendo arquivo: {stat_path}")

    
    status_info = {}
    try:
        with open(stat_path, 'r') as f:
            campos = f.read().split()

        utime = int(campos[13])     # campo 14: tempo em modo usuário
        stime = int(campos[14])     # campo 15: tempo em modo kernel
        tempo_total = utime + stime

        # Convertendo para segundos
        clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])  # normalmente 100
        tempo_segundos = tempo_total / clk_tck

        return {
            "utime_jiffies": utime,
            "stime_jiffies": stime,
            "tempo_total_jiffies": tempo_total,
            "tempo_total_segundos": round(tempo_segundos, 2)
        }
    except FileNotFoundError:
        print(f"Processo {processosID} não encontrado.")
        return None
    except PermissionError:
        print(f"Sem permissão para acessar {stat_path}.")
        return None    

def dicionarioStatCPUProcesso():
    """Retorna um dicionário com os status de todos os processos ativos"""
    processosCPU_info = {}
    for processosID in processosTodos():
        infoCPU = cpuProcesso(processosID)
        if infoCPU:  # Ignora processos que não puderam ser lidos
            processosCPU_info[processosID] = infoCPU
    return processosCPU_info



    #comentario na brach Matheus L
    #thayssa

