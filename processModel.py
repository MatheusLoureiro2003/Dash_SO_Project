import os
import pwd
import stat
import socket
import datetime # Para psutil e timestamp de criação (se psutil for usado)
import ctypes # p/ chamar semctl(2) via lib C
import ctypes.util # p/ encontrar a lib C
import struct

# Carrega a biblioteca C padrão para chamadas de sistema
libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True) #

# Variável global para armazenar informações globais de sockets de rede
_global_network_sockets_info = {} # NOVO: Cache global para informações de sockets


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
    """Retorna um dicionário com os status de todos os processos ativos, incluindo recursos abertos."""
    processos_info = {}
    # Atualiza o cache global de sockets de rede antes de processar os PIDs
    global _global_network_sockets_info # Declara uso da variável global
    _global_network_sockets_info = _ler_info_sockets_rede_global() # Preenche o cache global

    for processosID in processosTodos():
        info = statusProcesso(processosID)
        if info:
            # CORREÇÃO AQUI: Passar _global_network_sockets_info como argumento
            recursos_abertos = listar_recursos_abertos_processo(processosID, _global_network_sockets_info)
            info["recursos_abertos"] = recursos_abertos
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


# ----------------------- helpers POSIX ----------------------------
def list_posix_named_semaphores():
    """
    Escaneia /dev/shm em busca de semáforos POSIX nomeados (arquivos 'sem.*').
    Retorna lista de dicts com caminho, inode e permissões.
    """
    sems = []
    shm_path = "/dev/shm"
    try:
        if os.path.exists(shm_path) and os.path.isdir(shm_path):
            for fname in os.listdir(shm_path):
                if not fname.startswith("sem."):
                    continue
                full = os.path.join(shm_path, fname)
                try:
                    st = os.stat(full)
                    sems.append({
                        "tipo": "POSIX Nomeado",
                        "caminho": full,
                        "inode": st.st_ino,
                        "perms": oct(st.st_mode & 0o777),
                        "tamanho": st.st_size
                    })
                except (FileNotFoundError, PermissionError):
                    pass # Ignora arquivos que não podem ser acessados
    except (FileNotFoundError, PermissionError):
        pass # Ignora se /dev/shm não existe ou não pode ser acessado
    return sems

# ----------------------- helpers SYSV -----------------------------
class SemidDs(ctypes.Structure):    # struct semid_ds para semctl
    _fields_ = [
        ("sem_perm_uid", ctypes.c_uint32),  # uid
        ("sem_perm_gid", ctypes.c_uint32),  # gid
        ("sem_perm_mode", ctypes.c_uint16), # permissões
        ("__pad1", ctypes.c_uint16),        # preenchimento
        ("sem_nsems", ctypes.c_uint64),     # número de semáforos no conjunto
        ("__pad2", ctypes.c_uint64 * 2),    # preenchimento
    ]

# Constante para semctl (obter informações de status)
IPC_STAT = 2 #

def _semctl(semid_):
    """
    Chama semctl(2) para obter informações detalhadas de um conjunto de semáforos SysV.
    """
    ds = SemidDs()
    # semctl(semid, semnum, cmd, arg)
    # semnum = 0 (ignorado para IPC_STAT)
    # cmd = IPC_STAT
    # arg = ponteiro para struct semid_ds
    ret = libc.semctl(semid_, 0, IPC_STAT, ctypes.pointer(ds)) #
    if ret != 0:
        # Erro na chamada semctl, por exemplo, semid inválido ou permissão negada
        return None
    return {
        "semid": semid_,
        "nsems": ds.sem_nsems,
        "perms": oct(ds.sem_perm_mode & 0o777),
        "uid": ds.sem_perm_uid,
        "gid": ds.sem_perm_gid,
    }

def list_sysv_semaphores():
    """
    Lê /proc/sysvipc/sem e, quando possível, complementa com semctl().
    Retorna lista de dicionários com detalhes dos semáforos SysV.
    """
    sems = []
    try:
        with open("/proc/sysvipc/sem", 'r') as f: #
            next(f)  # Pula a linha do cabeçalho
            for line in f:
                parts = line.strip().split()
                if len(parts) < 4:
                    continue
                try:
                    semid = int(parts[0])
                    entry = {
                        "tipo": "SYSV",
                        "semid": semid,
                        "key": parts[1],
                        "perms_proc": parts[2], # Permissões como lidas do /proc
                        "nsems_proc": parts[3], # Número de semáforos como lido do /proc
                    }
                    # Tenta obter informações mais detalhadas via semctl
                    extra_info = _semctl(semid)
                    if extra_info:
                        entry.update(extra_info) # Adiciona/sobrescreve com dados de semctl
                    sems.append(entry)
                except ValueError:
                    pass # Ignora linhas mal formatadas
    except (FileNotFoundError, PermissionError):
        pass # Ignora se /proc/sysvipc/sem não existe ou não pode ser acessado
    return sems

# ------------------- helpers para classificação de FD e Sockets ----------------------
def _tipo_recurso_sem(real_path, target_stat):
    """
    Detecta se o real_path de um descritor de arquivo corresponde a semáforo POSIX anônimo ou nomeado.
    """
    if real_path.startswith('anon_inode:[sem]'): #
        return "POSIX Anônimo (Semaphore)"
    if real_path.startswith('/dev/shm/sem.'): #
        return "POSIX Nomeado (Semaphore)"
    return None

def _ler_info_sockets_rede_global():
    """
    Lê informações de sockets de rede globais do sistema de /proc/net/.
    Retorna um dicionário mapeando inodes de socket para seus detalhes.
    """
    sockets_info = {}
    socket_files = {
        "tcp": "/proc/net/tcp",
        "udp": "/proc/net/udp",
        "tcp6": "/proc/net/tcp6",
        "udp6": "/proc/net/udp6",
    }

    for proto, path in socket_files.items():
        try:
            with open(path, 'r') as f:
                next(f)
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 10:
                        continue
                    try:
                        local_addr_hex, local_port_hex = parts[1].split(':')
                        rem_addr_hex, rem_port_hex = parts[2].split(':')
                        st = int(parts[3], 16)
                        inode = int(parts[9])

                        local_ip = ''
                        if len(local_addr_hex) == 8: # IPv4
                            # CORREÇÃO AQUI: usar struct.pack
                            local_ip = socket.inet_ntoa(struct.pack("<L", int(local_addr_hex, 16))) #
                        elif len(local_addr_hex) == 32: # IPv6
                            local_ip = socket.inet_ntop(socket.AF_INET6, bytes.fromhex(local_addr_hex))
                        else:
                            local_ip = "N/A"

                        local_port = int(local_port_hex, 16)

                        remote_ip = ''
                        if len(rem_addr_hex) == 8: # IPv4
                            # CORREÇÃO AQUI: usar struct.pack
                            remote_ip = socket.inet_ntoa(struct.pack("<L", int(rem_addr_hex, 16))) #
                        elif len(rem_addr_hex) == 32: # IPv6
                            remote_ip = socket.inet_ntop(socket.AF_INET6, bytes.fromhex(rem_addr_hex))
                        else:
                            remote_ip = "N/A"

                        remote_port = int(rem_port_hex, 16)

                        sockets_info[inode] = {
                            "protocolo": proto,
                            "local_address": f"{local_ip}:{local_port}",
                            "remote_address": f"{remote_ip}:{remote_port}",
                            "state": _get_socket_state_name(st),
                            "inode": inode
                        }
                    except (ValueError, IndexError, socket.error, struct.error): # Adicionado struct.error
                        continue
        except (FileNotFoundError, PermissionError):
            continue
    return sockets_info

# _get_socket_state_name 
def _get_socket_state_name(state_hex_int):
    # Conteúdo da sua função _get_socket_state_name
    states = {
        1: "ESTABLISHED", 2: "SYN_SENT", 3: "SYN_RECV", 4: "FIN_WAIT1",
        5: "FIN_WAIT2", 6: "TIME_WAIT", 7: "CLOSE", 8: "CLOSE_WAIT",
        9: "LAST_ACK", 10: "LISTEN", 11: "CLOSING", 12: "NEW_SYN_RECV"
    }
    return states.get(state_hex_int, f"UNKNOWN({state_hex_int})")


# MARK: Função para listar recursos abertos por processo 
def listar_recursos_abertos_processo(pid, global_network_sockets_info):
    """
    Lista os descritores de arquivo abertos por um processo lendo o diretório /proc/[pid]/fd.
    Para cada descritor, tenta determinar o tipo (arquivo, socket, semáforo POSIX, pipe, etc.) e o caminho/identificador.
    Utiliza informações globais de sockets para detalhamento.
    Retorna um dicionário com listas de recursos categorizados.
    """
    recursos_abertos = {
        'pid': pid,
        'arquivos_regulares': [],
        'sockets': [],
        'pipes': [],
        'dispositivos': [],
        'semaphores_posix': [], # Para semáforos POSIX detectados via FD
        'links_quebrados_ou_inacessiveis': [],
        'outros': []
    }
    fd_path = f'/proc/{pid}/fd'

    try:
        for fd_num_str in os.listdir(fd_path):
            fd_num = int(fd_num_str)
            full_fd_path = os.path.join(fd_path, fd_num_str)

            try:
                real_path = os.readlink(full_fd_path)
                
                # Tenta obter o stat do ALVO do link simbólico
                target_stat = None
                try:
                    # os.stat segue o link simbólico
                    target_stat = os.stat(full_fd_path)
                except (FileNotFoundError, PermissionError):
                    pass # Se o alvo não existe ou sem permissão, target_stat permanece None

                tipo_recurso = "Desconhecido"
                detalhes = {
                    'fd': fd_num,
                    'caminho': real_path,
                    'modo': oct(target_stat.st_mode) if target_stat else 'N/A',
                    'inode': target_stat.st_ino if target_stat else 'N/A',
                    'tamanho': target_stat.st_size if target_stat and os.path.exists(real_path) else 'N/A',
                }

                # Prioridade na classificação: Semáforos POSIX, Sockets, Pipes, Dispositivos, Arquivos
                sem_tipo = _tipo_recurso_sem(real_path, target_stat)
                if sem_tipo:
                    detalhes['tipo'] = sem_tipo
                    recursos_abertos['semaphores_posix'].append(detalhes)
                elif real_path.startswith('socket:['): # Socket de domínio Unix ou outro
                    inode = int(real_path.split('[')[1][:-1]) if '[' in real_path else 'N/A'
                    socket_info = global_network_sockets_info.get(inode)
                    if socket_info:
                        detalhes['tipo'] = "Socket de Rede"
                        detalhes.update(socket_info)
                        recursos_abertos['sockets'].append(detalhes)
                    else:
                        detalhes['tipo'] = "Socket (Unix/Outro)"
                        recursos_abertos['sockets'].append(detalhes)
                elif real_path.startswith('pipe:['):
                    detalhes['tipo'] = "Pipe (FIFO)"
                    recursos_abertos['pipes'].append(detalhes)
                elif target_stat:
                    if stat.S_ISREG(target_stat.st_mode):
                        detalhes['tipo'] = "Arquivo Regular"
                        recursos_abertos['arquivos_regulares'].append(detalhes)
                    elif stat.S_ISDIR(target_stat.st_mode):
                        detalhes['tipo'] = "Diretório"
                        recursos_abertos['arquivos_regulares'].append(detalhes) # Pode ser uma categoria separada se quiser
                    elif stat.S_ISCHR(target_stat.st_mode):
                        detalhes['tipo'] = "Dispositivo de Caractere"
                        recursos_abertos['dispositivos'].append(detalhes)
                    elif stat.S_ISBLK(target_stat.st_mode):
                        detalhes['tipo'] = "Dispositivo de Bloco"
                        recursos_abertos['dispositivos'].append(detalhes)
                    elif stat.S_ISLNK(target_stat.st_mode):
                         # O alvo do link é outro link, tratamos como arquivo regular por simplicidade aqui
                        detalhes['tipo'] = "Link Simbólico (alvo)"
                        recursos_abertos['arquivos_regulares'].append(detalhes)
                    else:
                        detalhes['tipo'] = "Outro"
                        recursos_abertos['outros'].append(detalhes)
                else:
                    detalhes['tipo'] = "Link Quebrado/Inacessível"
                    recursos_abertos['links_quebrados_ou_inacessiveis'].append(detalhes)

            except (OSError, ValueError) as e:
                # Captura erros ao lerlink ou stat, indicando um link quebrado ou inacessível
                recursos_abertos['links_quebrados_ou_inacessiveis'].append({
                    'fd': fd_num_str,
                    'caminho': f"Erro ao ler link: {e}",
                    'tipo': 'Link Quebrado/Inacessível'
                })
    except (FileNotFoundError, PermissionError):
        pass # Diretório /proc/{pid}/fd não existe ou sem permissão

    return recursos_abertos


# MARK: Bloco de Teste Focado para processModel.py (Novas Funções)
if __name__ == "__main__":
    print("Iniciando testes focados em novas funcionalidades para processModel.py...\n")

    # --- Testando ler_info_sockets_rede_global() ---
    print("--- Teste: _ler_info_sockets_rede_global() ---")
    # Chama a função global diretamente para testar sua funcionalidade
    info_sockets_rede = _ler_info_sockets_rede_global() 
    print(f"Total de sockets de rede encontrados no sistema: {len(info_sockets_rede)}")
    
    if info_sockets_rede:
        print("\nAlguns exemplos de sockets de rede globais (inode: detalhes):")
        count = 0
        for inode, details in info_sockets_rede.items():
            print(f"  Inode: {inode}")
            print(f"    Protocolo: {details.get('protocolo', 'N/A')}")
            print(f"    Local: {details.get('local_address', 'N/A')}")
            print(f"    Remoto: {details.get('remote_address', 'N/A')}")
            print(f"    Estado: {details.get('state', 'N/A')}")
            count += 1
            if count >= 5: # Limita a exibição para os primeiros 5 para brevidade
                print("    ...(mais sockets)")
                break
    else:
        print("Nenhum socket de rede encontrado ou sem permissão para acessar /proc/net.")
    print("-" * 30 + "\n")

    # --- Testando list_posix_named_semaphores() ---
    print("--- Teste: list_posix_named_semaphores() ---")
    posix_sems = list_posix_named_semaphores()
    print(f"Total de semáforos POSIX nomeados encontrados: {len(posix_sems)}")
    if posix_sems:
        print("\nAlguns exemplos de semáforos POSIX nomeados:")
        for i, sem in enumerate(posix_sems[:5]):
            print(f"  {i+1}. Caminho: {sem['caminho']}, Inode: {sem['inode']}, Perms: {sem['perms']}, Tamanho: {sem['tamanho']} bytes")
        if len(posix_sems) > 5:
            print("  ...(mais semáforos POSIX nomeados)")
    else:
        print("Nenhum semáforo POSIX nomeado detectado ou sem permissão para /dev/shm.")
    print("-" * 30 + "\n")

    # --- Testando list_sysv_semaphores() ---
    print("--- Teste: list_sysv_semaphores() ---")
    sysv_sems = list_sysv_semaphores()
    print(f"Total de semáforos System V encontrados: {len(sysv_sems)}")
    if sysv_sems:
        print("\nAlguns exemplos de semáforos System V:")
        for i, sem in enumerate(sysv_sems[:5]):
            detail_str = f"SemID: {sem['semid']}, Chave: {sem['key']}"
            if 'nsems' in sem: # Se semctl conseguiu detalhes
                detail_str += f", N. Semáforos: {sem['nsems']}, Perms: {sem['perms']}, UID: {sem['uid']}, GID: {sem['gid']}"
            else: # Se apenas /proc/sysvipc/sem foi lido
                 detail_str += f", N. Semáforos (proc): {sem['nsems_proc']}, Perms (proc): {sem['perms_proc']}"
            print(f"  {i+1}. {detail_str}")
        if len(sysv_sems) > 5:
            print("  ...(mais semáforos System V)")
    else:
        print("Nenhum semáforo System V detectado ou sem permissão para /proc/sysvipc/sem.")
    print("-" * 30 + "\n")


    # --- Testando dicionarioStatusProcesso() com foco em recursos_abertos (incluindo sockets e semáforos) ---
    print("--- Teste: dicionarioStatusProcesso() (foco em recursos abertos aprimorados) ---")
    # dicionarioStatusProcesso() já inicializa _global_network_sockets_info
    status_processos_com_recursos = dicionarioStatusProcesso()
    print(f"Número de processos com status e recursos coletados: {len(status_processos_com_recursos)}")

    # Tenta encontrar um PID com recursos abertos interessantes
    pid_exemplo_recursos = None
    for pid, info in status_processos_com_recursos.items():
        recursos_categorizados = info.get('recursos_abertos', {})
        if (recursos_categorizados.get('semaphores_posix') or
            recursos_categorizados.get('sockets') or
            recursos_categorizados.get('pipes') or
            recursos_categorizados.get('dispositivos') or
            recursos_categorizados.get('arquivos_regulares')): # Garantir que tenha algum recurso
            pid_exemplo_recursos = pid
            break
    
    # Fallback para o primeiro PID se nenhum com recursos interessantes for encontrado
    if not pid_exemplo_recursos and processosTodos():
        pid_exemplo_recursos = processosTodos()[0]

    if pid_exemplo_recursos and pid_exemplo_recursos in status_processos_com_recursos:
        print(f"\nDetalhes de Recursos Abertos para PID de exemplo ({pid_exemplo_recursos}):")
        exemplo_info = status_processos_com_recursos[pid_exemplo_recursos]
        print(f"  Nome do Processo: {exemplo_info.get('nome', 'N/A')}")
        
        recursos = exemplo_info.get('recursos_abertos', {}) # Agora é um dicionário categorizado
        
        # Lista todas as categorias de recursos
        categorias_existentes = False
        for category, items in recursos.items():
            if items and category != 'pid': # 'pid' não é uma categoria de recursos para listar
                categorias_existentes = True
                print(f"\n  Categoria: {category.replace('_', ' ').title()}: ({len(items)} itens)")
                # Exibe até 5 itens por categoria para brevidade
                for i, item in enumerate(items[:5]): 
                    display_str = f"    - FD {item.get('fd', 'N/A')}: Tipo: {item.get('tipo', 'N/A')}"
                    if item.get('caminho'):
                        display_str += f", Caminho/Destino: {item['caminho']}"
                    if item.get('protocolo'): # Para sockets
                        display_str += f", Proto: {item['protocolo']}, Local: {item['local_address']}, Remoto: {item['remote_address']}, Estado: {item['state']}"
                    print(display_str)
                    if 'inode' in item: # Adicionar inode para todos os tipos relevantes
                         print(f"      Inode: {item['inode']}")
                    print("      ---")
                if len(items) > 5:
                    print(f"    ...(mais {len(items) - 5} itens nesta categoria)")
        
        if not categorias_existentes:
            print("  Nenhum recurso aberto detectado ou acesso negado para este processo.")

    else:
        print("\nNão foi possível obter detalhes de recursos para um PID de exemplo ou nenhum processo ativo com recursos.")
    print("-" * 30 + "\n")

    print("Testes focados concluídos para processModel.py.")