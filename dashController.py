import threading
import time
import tkinter as tk
import os
from view import dashboard_view, atualizar_interface
from cpuModel import lerUsoCpu
from memoryModel import lerUsoMemoria
from processModel import dicionarioStatusProcesso, dicionarioStatCPUProcesso, atualizar_cpu_total, dicionarioPaginaProcesso,ler_cpu_total, processosTodos, cpuProcesso


# Locks para controle de concorrência
lock_cpu = threading.Lock() # lock para sincronizar acessos relacionados à leitura/atualização dos dados da CPU
lock_mem = threading.Lock() # lock para sincronizar acessos relacionados à leitura/atualização dos dados de memória
lock_proc = threading.Lock() # lock para sincronizar acessos relacionados à leitura/atualização dos dados dos processos

# Dados compartilhados entre threads
dados_cpu = {}  # dicionário para guardar estatísticas atuais da CPU
dados_mem = {}   # dicionário para guardar estatísticas atuais da memória
dados_proc = {}  # dicionário para guardar estatísticas ou dos processos em execução


# Funções que atualizam os dados em paralelo

def atualizar_cpu():
    global dados_cpu                  # declara que vai usar a variável global dados_cpu
    while True:                      # loop infinito para atualizar os dados continuamente
        uso, ocioso = lerUsoCpu()   # chama função que retorna uso e ociosidade da CPU em percentual
        with lock_cpu:               # entra na seção crítica protegida pelo lock para evitar condição de corrida
            dados_cpu = {            # atualiza o dicionário global com os novos valores de uso e ociosidade
                "uso_cpu_percent": uso,
                "ociosidade_percent": ocioso
            }
        time.sleep(5)                # pausa a execução por 5 segundos antes de atualizar novamente



def atualizar_memoria():
    global dados_mem            # declara que vai usar a variável global dados_mem
    while True:                 # loop infinito para atualizar os dados continuamente
        mem = lerUsoMemoria()   # chama função que retorna o uso atual da memória
        with lock_mem:          # entra na seção crítica protegida pelo lock para evitar acesso concorrente
            dados_mem = mem     # atualiza o dicionário global com os dados de memória obtidos
        time.sleep(5)           # pausa a execução por 5 segundos antes de atualizar novamente

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

# MARK: Função que atualiza os processos em execução

def atualizar_processos():
    global dados_proc
    prev_cpu_total = None
    prev_proc_times = {}
    while True:
        print("Atualizando processos...")
        # Foto inicial se ainda não existir
        cpu0, proc0 = snapshot()
        if prev_cpu_total is None:
            prev_cpu_total, prev_proc_times = cpu0, proc0
            time.sleep(5)
            continue
        # Nova foto e cálculo de uso
        cpu1, proc1 = snapshot()
        usos = calcular_usos(prev_cpu_total, prev_proc_times, cpu1, proc1)
        prev_cpu_total, prev_proc_times = cpu1, proc1

        # Coleta as demais informações
        status = dicionarioStatusProcesso()
        cpu = dicionarioStatCPUProcesso()
        paginas = dicionarioPaginaProcesso()

        processos = {}
        for pid in status:
            if pid in cpu and pid in paginas and pid in usos:
                processos[pid] = {
                    **status[pid],
                    **cpu[pid],
                    "uso_percentual_cpu": usos[pid],
                    **paginas[pid]
                }
        with lock_proc:
            dados_proc = processos
        time.sleep(5)

# def atualizar_processos():
#     global dados_proc               # declara que vai usar a variável global dados_proc
#     while True:                    # loop infinito para atualizar os dados continuamente
#         print("Atualizando processos...")  # mensagem de log para indicar que a atualização começou

#         atualizar_cpu_total()      # atualiza o delta do tempo total da CPU para cálculos de uso

#         status = dicionarioStatusProcesso()  # obtém informações do status atual de todos os processos
#         cpu = dicionarioStatCPUProcesso()    # obtém o uso percentual da CPU e tempo de uso da CPU para todos os processos
#         paginas = dicionarioPaginaProcesso() # obtém informação da quantidade total de páginas para todos os processos

#         processos = {}             # cria dicionário temporário para armazenar dados combinados dos processos
#         for pid in status:         # para cada PID no status dos processos
#             if pid in cpu and pid in paginas:         # verifica se também temos dados de CPU para esse PID
#                 # une os dados de status e CPU para o mesmo processo em um único dicionário
#                 processos[pid] = {**status[pid], **cpu[pid], **paginas[pid]}

#         with lock_proc:            # entra na seção crítica para evitar condições de corrida ao atualizar dados
#             dados_proc = processos  # atualiza o dicionário global com os dados mais recentes dos processos

#         time.sleep(5)              # pausa 5 segundos antes de repetir a atualização


# MARK: Função que inicia o loop de exibição da interface gráfica

def loop_exibicao():
    def atualizar():
        with lock_cpu:                   # bloqueia acesso à dados_cpu para leitura segura
            cpu = dados_cpu.copy()       # faz uma cópia dos dados atuais da CPU
        
        with lock_mem:                   # bloqueia acesso à dados_mem para leitura segura
            mem = dados_mem.copy()       # faz uma cópia dos dados atuais da memória
        
        with lock_proc:                  # bloqueia acesso à dados_proc para leitura segura
            procs = dados_proc.copy()    # faz uma cópia dos dados atuais dos processos

        atualizar_interface(cpu, mem, procs)  # atualiza a interface gráfica com os dados copiados
        
        root.after(1000, atualizar)      # agenda a próxima atualização da interface para daqui 1 segundo

    global root
    root = tk.Tk()                       # cria a janela principal do Tkinter
    dashboard_view(root, dados_cpu, dados_mem, dados_proc)  # inicializa a interface (widgets etc.)
    root.after(1000, atualizar)          # agenda a primeira atualização da interface para daqui 1 segundo
    root.mainloop()                     # inicia o loop principal da interface gráfica Tkinter



def iniciar_controller():
    threading.Thread(target=atualizar_cpu, daemon=True).start()  # inicia thread em segundo plano para atualizar dados da CPU continuamente
    threading.Thread(target=atualizar_memoria, daemon=True).start()  # inicia thread em segundo plano para atualizar dados da memória continuamente
    threading.Thread(target=atualizar_processos, daemon=True).start()  # inicia thread em segundo plano para atualizar dados dos processos continuamente

    loop_exibicao() # inicia o loop principal da interface gráfica (bloqueante)
