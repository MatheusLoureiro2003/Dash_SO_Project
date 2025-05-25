import threading
import time

from cpuModel import lerUsoCpu
from memoryModel import lerUsoMemoria
from processModel import dicionarioStatusProcesso, dicionarioStatCPUProcesso
from terminalView 

# Locks para controle de concorrência (caso precise usar dados globais)
lock_cpu = threading.Lock()
lock_mem = threading.Lock()
lock_proc = threading.Lock()

# Dados compartilhados entre threads
dados_cpu = {}
dados_mem = {}
dados_proc = {}

# Funções que atualizam os dados ciclicamente

def atualizar_cpu():
    global dados_cpu
    while True:
        uso, ocioso = lerUsoCpu()
        with lock_cpu:
            dados_cpu = {
                "uso_cpu_percent": uso,
                "ociosidade_percent": ocioso
            }
        time.sleep(5)

def atualizar_memoria():
    global dados_mem
    while True:
        mem = lerUsoMemoria()
        with lock_mem:
            dados_mem = mem
        time.sleep(5)

def atualizar_processos():
    global dados_proc
    while True:
        status = dicionarioStatusProcesso()
        cpu = dicionarioStatCPUProcesso()
        processos = {}
        for pid in status:
            if pid in cpu:
                processos[pid] = {**status[pid], **cpu[pid]}
        with lock_proc:
            dados_proc = processos
        time.sleep(5)

# Função que chama a view com dados atualizados

def loop_exibicao():
    while True:
        with lock_cpu:
            cpu = dados_cpu.copy()
        with lock_mem:
            mem = dados_mem.copy()
        with lock_proc:
            procs = dados_proc.copy()

        exibir_dashboard(cpu, mem, procs)
        time.sleep(1)

# Função principal

def iniciar_dashboard():
    threading.Thread(target=atualizar_cpu, daemon=True).start()
    threading.Thread(target=atualizar_memoria, daemon=True).start()
    threading.Thread(target=atualizar_processos, daemon=True).start()

    loop_exibicao()
