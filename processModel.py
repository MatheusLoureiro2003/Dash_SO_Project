import os
import pwd


# Estado interno para armazenar valores anteriores
prev_cpu_total = None    # armazena o último valor total lido do tempo da CPU (em jiffies)
                         # usado para calcular o delta entre leituras sucessivas
previo_processo_CPU = {}    # dicionário que mapeia ProcessoID de processos para seu último tempo total de CPU registrado
                         # usado para calcular a variação do tempo CPU por processo entre chamadas
delta_cpu_total = None    # armazena a diferença do tempo total da CPU entre a última e penúltima leitura
                         # usado para calcular percentuais relativos de uso da CPU

# MARK: Funções que lista todos os do sistema

def processosTodos():
    """Retorna e imprime uma lista de todos os PIDs encontrados em /proc"""

    processosID = [processosID for processosID in os.listdir('/proc') if processosID.isdigit()] #lista os processos do diretorio proc, verifica se todos os processos são dígitos.
  
    return processosID 


# MARK: Funções que lêem os dados de cada processo

def statusProcesso(processosID):

    """Lê e retorna os dados do arquivo /proc/[pid]/status como dicionário"""

    status_path = f'/proc/{processosID}/status' #caminho para acessar valores de cada processo
    status_info = {} #onde serão guardadas os valores do processo

    try: # Abre o arquivo status_path para leitura de forma segura,
    # garantindo que o arquivo será fechado automaticamente após o uso

        with open(status_path, 'r') as f: 

            for linha in f:#itera sobre cada linha de status do processo, 
                            #realiza uma condicional e armazena o valor de destaque no vetor status_info

                if linha.startswith("Name:"):
                    status_info["nome"] = linha.split()[1]

                elif linha.startswith("State:"):
                    status_info["estado"] = " ".join(linha.split()[1:])

                elif linha.startswith("Uid:"):
                    uid = int(linha.split()[1]) 
                    status_info["usuario"] = pwd.getpwuid(uid).pw_name #Acessa o banco de dados e pega o Usuario Id 
                                                                        #correspondente e seleciona o nome desse usuário
                                                                        
                elif linha.startswith("Threads:"):
                    status_info["threads"] = int(linha.split()[1])

                elif linha.startswith("VmSize:"):#memoria total
                    status_info["mem_total_kb"] = int(linha.split()[1])

                elif linha.startswith("VmRSS:"):#memoria residente
                    status_info["mem_residente_kb"] = int(linha.split()[1])

                elif linha.startswith("VmData:"):#memoria heap
                    status_info["mem_heap_kb"] = int(linha.split()[1])

                elif linha.startswith("VmStk:"):#memoria stack
                    status_info["mem_stack_kb"] = int(linha.split()[1])

                elif linha.startswith("VmExe:"):#memoria de código
                    status_info["mem_codigo_kb"] = int(linha.split()[1])

    except FileNotFoundError:
        print(f"Processo {processosID} não existe ou terminou.")
        return None
    
    except PermissionError:#exceção
        print(f"Sem permissão para acessar {status_path} (PermissionError)")
        return None

    return status_info # Retorna o dicionário com as informações do processo


# MARK: Funções que retornam dicionários com os dados de todos os processos ativos

def dicionarioStatusProcesso():
    """Retorna um dicionário com os status de todos os processos ativos"""

    processos_info = {}
    
    for processosID in processosTodos():
        info = statusProcesso(processosID)

        if info:  # Ignora processos que não puderam ser lidos
            processos_info[processosID] = info

    return processos_info


# MARK: Funções que lêem o uso da CPU de cada processo

def cpuProcesso(processosID):

    """Lê e retorna os dados do arquivo /proc/[pid]/stat como dicionário"""

    stat_path = f'/proc/{processosID}/stat'
    
    try:

        with open(stat_path, 'r') as f:

            campos = f.read().split()

        utime = int(campos[13])     # campo 14: tempo em modo usuário
        stime = int(campos[14])     # campo 15: tempo em modo kernel

        tempo_total = utime + stime

        # Convertendo para segundos
        clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])  # normalmente 100
        tempo_segundos = tempo_total / clk_tck #calcula o tempo de jiffs em segundos

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


#prev_cpu_total = None 
#previo_processo_CPU = {}    
#delta_cpu_total = None   

# MARK: Funções que lêem o tempo total da CPU do sistema em jiffies

def ler_cpu_total(): 

    with open("/proc/stat", "r") as f: #caminho com o valor do uso da cpu global

        linha = f.readline()
        valores = list(map(int, linha.split()[1:])) # converte os tempos para inteiros, ignorando o label 'cpu'
        return sum(valores) # soma e retorna o total dos jiffies da CPU


# MARK: Funções que atualizam o uso da CPU e processos calculando o delta 

def atualizar_cpu_total():

    """Atualiza o delta(diferença) global do tempo total da CPU. Deve ser chamado uma vez por ciclo."""

    global prev_cpu_total, delta_cpu_total # usa as variáveis globais para manter o estado entre chamadas

    cpu_total_atual = ler_cpu_total() # lê o valor total atual do tempo da CPU (em jiffies)

    if prev_cpu_total is None: # se for a primeira vez que a função é chamada

        prev_cpu_total = cpu_total_atual # armazena o valor atual como referência para próximas leituras
        delta_cpu_total = 0  # delta inicial é zero, pois não há leitura anterior para comparar
        return 0  # retorna zero pois não há variação calculável ainda
    
    delta_cpu_total = cpu_total_atual - prev_cpu_total # calcula a diferença desde a última leitura
    prev_cpu_total = cpu_total_atual # atualiza o valor armazenado para próxima chamada

    return delta_cpu_total  # retorna o delta calculado (variação do tempo CPU)


# MARK: Funções que calculam o uso da CPU por processo

def calcular_uso_cpu_processo(pid):

    global previo_processo_CPU, delta_cpu_total  # usa variáveis globais para manter dados entre chamadas

    proc_info = cpuProcesso(pid) # obtém informações atuais do processo pelo ProcessoID

    if proc_info is None: #se o processo não existir ou info não disponível
        return 0.0 #retorna uso 0.0 para evitar erro
    
    proc_total_atual = proc_info['tempo_total_jiffies'] # extrai o tempo total da CPU usado pelo processo (em jiffies)

    if pid not in previo_processo_CPU:  # se for a primeira vez que vemos esse ProcessoID

        previo_processo_CPU[pid] = proc_total_atual # armazena o tempo atual para próximas comparações
        return 0.0  # retorna 0.0 pois não tem dado anterior para calcular delta

    delta_processos = proc_total_atual - previo_processo_CPU[pid] # calcula a variação do tempo CPU do processo
    previo_processo_CPU[pid] = proc_total_atual # atualiza o valor armazenado para a próxima chamada

    if delta_cpu_total and delta_cpu_total > 0:  # verifica se o delta total da CPU está disponível e é válido
        uso = (delta_processos / delta_cpu_total) * 100 
    else:
        uso = 0.0 # se não tiver delta válido, considera uso 0
        uso = 0.0 # se não tiver delta válido, considera uso 0

    return round(uso, 2)  # retorna o uso arredondado com 2 casas decimais
    return round(uso, 2)  # retorna o uso arredondado com 2 casas decimais


# MARK: Funções que retornam dicionários com o uso da CPU de todos os processos ativos

def dicionarioStatCPUProcesso():

    """Retorna um dicionário com o uso percentual da CPU de todos os processos ativos"""
    processosCPU_info = {}  

    for pid in processosTodos():  

        uso_percentual = calcular_uso_cpu_processo(pid) # calcula o uso percentual da CPU para o processo atual

        tempo_cpu = cpuProcesso(pid)  # obtém as informações detalhadas do uso de CPU do processo

        if tempo_cpu is not None:  # verifica se as informações do processo foram obtidas com sucesso

            processosCPU_info[pid] = { # adiciona ao dicionário o PID como chave e um novo dicionário com as infos + uso percentual
                **tempo_cpu,  # copia todas as informações do tempo_cpu para o novo dicionário o ** desempacota o dicionário
                "uso_percentual_cpu": uso_percentual  # adiciona o uso percentual de CPU como um campo extra
            }
    return processosCPU_info # retorna o dicionário com os dados de todos os processos ativos

def snapshot():
    """Tira uma foto de jiffies da CPU total e de cada processo."""
    cpu_total = ler_cpu_total()
    proc_times = {}
    for pid in processosTodos(): 
        info = cpuProcesso(pid)
        if info is not None:
            proc_times[pid] = info["tempo_total_jiffies"]
    return cpu_total, proc_times


def calcular_usos(cpu0, proc0, cpu1, proc1):
    """Calcula o uso percentual da CPU de cada processo entre duas fotos."""
    delta_cpu = cpu1 - cpu0
    cores = os.cpu_count() or 1
    usos = {}
    if delta_cpu <= 0:
        return usos
    for pid, t0 in proc0.items():
        t1 = proc1.get(pid)
        if t1 is None:
            continue
        delta_p = t1 - t0
        uso = (delta_p / delta_cpu) * 100 * cores
        usos[pid] = round(max(0.0, min(uso, 100.0)), 2)
    return usos



# MARK: Funções que lêem a quantidade de páginas usadas por cada processo

def paginaProcesso(processosID):

    """Lê e retorna a quantidade de páginas usadas pelo processo a partir do arquivo /proc/[pid]/statm"""
    
    statm_path = f'/proc/{processosID}/statm'  

    try:

        with open(statm_path, 'r') as f:
            # Lê o conteúdo e divide os valores
            campos = f.read().split()
        
        total_pagina = int(campos[0])  # O primeiro campo de statm é o tamanho total do processo em páginas (tamanho virtual)

        return {
            "total_pagina": total_pagina 
        }
    
    except FileNotFoundError:  
        print(f"Processo {processosID} não encontrado.")
        return None
    
    except PermissionError:  
        print(f"Sem permissão para acessar {statm_path}.")
        return None


# MARK: Funções que retornam dicionários com a quantidade de páginas usadas por todos os processos ativos

def dicionarioPaginaProcesso():
    """Retorna um dicionário com a quantidade de páginas usadas por todos os processos ativos"""
    processos_pagina_info = {}  # Dicionário onde serão armazenadas as informações de páginas dos processos
    for processosID in processosTodos(): 
        pagina_info = paginaProcesso(processosID)  # Chama a função que retorna a quantidade de páginas
        if pagina_info:  
            processos_pagina_info[processosID] = pagina_info  # Adiciona o PID e a quantidade de páginas no dicionário
    return processos_pagina_info  # Retorna o dicionário com as informações de páginas de todos os processos


# MARK: Função que conta o número total de processos e threads ativos

def contar_processos_e_threads():
    """
    Calcula o número total de processos ativos e o número total de threads.
    Retorna uma tupla: (total_processos, total_threads).
    """
    lista_pids = processosTodos()
    
    if not lista_pids:
        return 0, 0

    total_processos = len(lista_pids)
    total_threads = 0

    for pid in lista_pids:
        info_proc = statusProcesso(pid) # retorna informações do processo como dicionário

        if info_proc and "threads" in info_proc:
            try:
                total_threads += int(info_proc["threads"]) 
            except (ValueError, TypeError):
                # Ocorre se 'threads' não for um número válido; ignora o processo para a soma de threads.
                pass 
    return total_processos, total_threads
