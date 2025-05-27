import os

def processosTodos():
    """Retorna e imprime uma lista de todos os PIDs encontrados em /proc"""
    processosID = [processosID for processosID in os.listdir('/proc') if processosID.isdigit()] #lista os processos do diretorio proc, verifica se todos os processos são dígitos.
    # print("processosID encontrados:", processosID)
    return processosID


import pwd

def statusProcesso(processosID):
    """Lê e retorna os dados do arquivo /proc/[pid]/status como dicionário"""

    status_path = f'/proc/{processosID}/status'
    status_info = {}

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



# Estado interno para armazenar valores anteriores
prev_cpu_total = None
prev_proc_totals = {}
prev_cpu_delta = None

def ler_cpu_total():
    with open("/proc/stat", "r") as f:
        linha = f.readline()
        valores = list(map(int, linha.split()[1:]))
        return sum(valores)

def atualizar_cpu_total():
    """Atualiza o delta global do tempo total da CPU. Deve ser chamado uma vez por ciclo."""
    global prev_cpu_total, prev_cpu_delta
    cpu_total_atual = ler_cpu_total()
    if prev_cpu_total is None:
        prev_cpu_total = cpu_total_atual
        prev_cpu_delta = 0
        return 0
    prev_cpu_delta = cpu_total_atual - prev_cpu_total
    prev_cpu_total = cpu_total_atual
    return prev_cpu_delta

def calcular_uso_cpu_processo(pid):
    global prev_proc_totals, prev_cpu_delta

    proc_info = cpuProcesso(pid)
    if proc_info is None:
        return 0.0
    proc_total_atual = proc_info['tempo_total_jiffies']

    if pid not in prev_proc_totals:
        prev_proc_totals[pid] = proc_total_atual
        return 0.0

    proc_delta = proc_total_atual - prev_proc_totals[pid]
    prev_proc_totals[pid] = proc_total_atual

    num_cores = os.cpu_count() or 1
    if prev_cpu_delta and prev_cpu_delta > 0:
        uso = (proc_delta / prev_cpu_delta) * 100 * num_cores
    else:
        uso = 0.0

    return round(uso, 2)


def dicionarioStatCPUProcesso():
    """Retorna um dicionário com o uso percentual da CPU de todos os processos ativos"""
    processosCPU_info = {}
    for pid in processosTodos():
        uso_percentual = cpuProcesso(pid)  # sua função que calcula a % de CPU
        if uso_percentual is not None:
            processosCPU_info[pid] = uso_percentual
    return processosCPU_info




