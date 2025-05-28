import threading
import time
import tkinter as tk

from view import dashboard_view, atualizar_interface
from cpuModel import lerUsoCpu
from memoryModel import lerUsoMemoria
from processModel import dicionarioStatusProcesso, dicionarioStatCPUProcesso, atualizar_cpu_total, dicionarioPaginaProcesso


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



def atualizar_processos():
    global dados_proc               # declara que vai usar a variável global dados_proc
    while True:                    # loop infinito para atualizar os dados continuamente
        print("Atualizando processos...")  # mensagem de log para indicar que a atualização começou

        atualizar_cpu_total()      # atualiza o delta do tempo total da CPU para cálculos de uso

        status = dicionarioStatusProcesso()  # obtém informações do status atual de todos os processos
        cpu = dicionarioStatCPUProcesso()    # obtém o uso percentual da CPU e tempo de uso da CPU para todos os processos
        paginas = dicionarioPaginaProcesso() # obtém informação da quantidade total de páginas para todos os processos

        processos = {}             # cria dicionário temporário para armazenar dados combinados dos processos
        for pid in status:         # para cada PID no status dos processos
            if pid in cpu and pid in paginas:         # verifica se também temos dados de CPU para esse PID
                # une os dados de status e CPU para o mesmo processo em um único dicionário
                processos[pid] = {**status[pid], **cpu[pid], **paginas[pid]}

        with lock_proc:            # entra na seção crítica para evitar condições de corrida ao atualizar dados
            dados_proc = processos  # atualiza o dicionário global com os dados mais recentes dos processos

        time.sleep(5)              # pausa 5 segundos antes de repetir a atualização



# Loop que atualiza a interface gráfica periodicamente

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

# Função principal que inicia tudo

def iniciar_controller():
    threading.Thread(target=atualizar_cpu, daemon=True).start()  # inicia thread em segundo plano para atualizar dados da CPU continuamente
    threading.Thread(target=atualizar_memoria, daemon=True).start()  # inicia thread em segundo plano para atualizar dados da memória continuamente
    threading.Thread(target=atualizar_processos, daemon=True).start()  # inicia thread em segundo plano para atualizar dados dos processos continuamente

    loop_exibicao() # inicia o loop principal da interface gráfica (bloqueante)
