import threading
import time
import tkinter as tk

from view import dashboard_view, atualizar_interface
from cpuModel import lerUsoCpu
from memoryModel import lerUsoMemoria
from processModel import dicionarioStatusProcesso, dicionarioStatCPUProcesso, atualizar_cpu_total


# Locks para controle de concorrência
lock_cpu = threading.Lock()
lock_mem = threading.Lock()
lock_proc = threading.Lock()

# Dados compartilhados entre threads
dados_cpu = {}
dados_mem = {}
dados_proc = {}


# Funções que atualizam os dados em paralelo

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
        print("Atualizando processos...")

        atualizar_cpu_total()

        status = dicionarioStatusProcesso()
        cpu = dicionarioStatCPUProcesso()
        
        processos = {}
        for pid in status:
            if pid in cpu:
                processos[pid] = {**status[pid], **cpu[pid]}
        with lock_proc:
            dados_proc = processos
        time.sleep(5)


# Loop que atualiza a interface

def loop_exibicao():
    def atualizar():
        with lock_cpu:
            cpu = dados_cpu.copy()
        with lock_mem:
            mem = dados_mem.copy()
        with lock_proc:
            procs = dados_proc.copy()

        atualizar_interface(cpu, mem, procs)
        root.after(1000, atualizar)  # atualiza a cada 1 segundo

    global root
    root = tk.Tk()
    dashboard_view(root, dados_cpu, dados_mem, dados_proc)
    root.after(1000, atualizar)  # primeira atualização após 1 segundo
    root.mainloop()


# Função principal que inicia tudo

def iniciar_controller():
    threading.Thread(target=atualizar_cpu, daemon=True).start()
    threading.Thread(target=atualizar_memoria, daemon=True).start()
    threading.Thread(target=atualizar_processos, daemon=True).start()

    loop_exibicao()
