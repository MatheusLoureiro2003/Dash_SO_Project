import threading
import time
import tkinter as tk
from view import dashboard_view, atualizar_interface
from cpuModel import lerUsoCpu
from memoryModel import lerUsoMemoria
from processModel import (dicionarioStatusProcesso, dicionarioStatCPUProcesso, 
                          atualizar_cpu_total, dicionarioPaginaProcesso,
                          contar_processos_e_threads) 
from systemModel import listDirectoryContent

# Locks para controle de concorrência, que sincronizam o acesso relacionado à leitura/atualização dos dados

lock_cpu = threading.Lock() 
lock_mem = threading.Lock() 
lock_proc = threading.Lock() 


# Dados compartilhados entre threads armazenados em dicionários globais

dados_cpu = {}  
dados_mem = {}   
dados_proc = {}

def atualizar_diretorio(diretorio_caminho="/"):
    global dados_diretorio

    conteudo = listDirectoryContent(diretorio_caminho)
    return conteudo
  
# MARK: Funções que atualizam os dados da CPU em paralelo
def atualizar_cpu():
    global dados_cpu 

    while True:

        uso_percent, ocioso_percent = lerUsoCpu()
        
        # Chamada para obter contagens globais (tupla)
        total_procs, total_thrs = contar_processos_e_threads()

        with lock_cpu:    # entra na seção crítica protegida pelo lock para evitar condição de corrida
            dados_cpu = {
                "uso_cpu": uso_percent,
                "ocioso": ocioso_percent,
                "total_processos": total_procs,  
                "total_threads": total_thrs   
            }
        
        time.sleep(5)



# MARK: Funções que atualizam os dados da memória e dos processos em paralelo

def atualizar_memoria():
    global dados_mem            

    while True:        

        mem = lerUsoMemoria()   # chama função que retorna um dicionario do uso atual da memória

        with lock_mem:          # entra na seção crítica protegida pelo lock para evitar acesso concorrente
            dados_mem = mem     # atualiza o dicionário global com os dados de memória obtidos
        time.sleep(5)           


# MARK: Função que atualiza os dados dos processos

def atualizar_processos():

    global dados_proc               

    while True:                   

        atualizar_cpu_total()      # atualiza o delta do tempo total da CPU para 
                                    #cálculos de uso (diferença entre dois tempos de leitura global)

        status = dicionarioStatusProcesso()  
        cpu = dicionarioStatCPUProcesso()    
        paginas = dicionarioPaginaProcesso() 

        processos = {}             # Armazenar dados combinados dos processos

        for pid in status:         # para cada PID no status dos processos

            if pid in cpu and pid in paginas:         # verifica se também temos dados de CPU e dados 
                                                        #de pagina para esse PID

                # une os dados de status, CPU e pagina para o mesmo processo em um único dicionário
                processos[pid] = {**status[pid], **cpu[pid], **paginas[pid]}

        processos_ordenados = dict(sorted(processos.items(), key=lambda item: item[1].get("uso_percentual_cpu", 0), reverse=True))

        with lock_proc:
            dados_proc = processos_ordenados
        time.sleep(5)              


# MARK: Função que inicia o loop de exibição da interface gráfica

def loop_exibicao():

    def atualizar():

        with lock_cpu:                  
            cpu = dados_cpu.copy()       # faz uma cópia dos dados atuais da CPU 
                                            #(copia para evitar problemas de concorrência)
        
        with lock_mem:                  
            mem = dados_mem.copy()       
        
        with lock_proc:                  
            procs = dados_proc.copy()    

        atualizar_interface(cpu, mem, procs)  
        
        root.after(1000, atualizar)      # agenda a próxima atualização da interface para daqui 1 segundo

    global root   # variável global para armazenar a janela principal do Tkinter

    root = tk.Tk()                       # cria a janela principal do Tkinter

    dashboard_view(root, dados_cpu, dados_mem, dados_proc, atualizar_diretorio)  # inicializa a interface (widgets etc.)
    root.after(1000, atualizar)          # agenda a primeira atualização da interface para daqui 1 segundo
    root.mainloop()                     # inicia o loop principal da interface gráfica Tkinter



# MARK: Função que inicia todos os threads e o loop de exibição da interface gráfica

def iniciar_controller():

    # inicia thread em segundo plano para atualizar dados da CPU continuamente
    threading.Thread(target=atualizar_cpu, daemon=True).start()  
    threading.Thread(target=atualizar_memoria, daemon=True).start()  
    threading.Thread(target=atualizar_processos, daemon=True).start()  

    loop_exibicao() # inicia o loop principal da interface gráfica (bloqueante)


