import threading
import time

lock = threading.Lock() #trava que controla o acesso seguro a recursos compartilhados em threads.
uso_cpu_global = None


def lerUsoCpu():

    '''
     'proc' arquivos de interface do kernel
     /proc/stat arquivo com estatísticas sobre o uso da CPU
     usoCPU = 100% - tempo_ocioso / tempo_total

    '''

    with open("/proc/stat", "r") as f:
        linha = f.readline() 
        partes1 = linha.split()[1:]
        valores1 = list(map(int, partes1))
        
    time.sleep(5) #bloqueante

    with open("/proc/stat", "r") as f:
        linha = f.readline()
        partes2 = linha.split()[1:]
        valores2 = list(map(int, partes2))

    tempo1 = sum(valores1) #soma de todos os tempos registrados
    tempo2 = sum(valores2)

    tempoOcioso1 = valores1[3]
    tempoOcioso2 = valores2[3]

    tempoDiff = tempo2 - tempo1
    idleDiff = tempoOcioso2 - tempoOcioso1 ##idle -> tempo de ociosidade da CPU

    tempoAtivo = tempoDiff - idleDiff #tempo em que a CPU realmente trabalhou

    usoCpu = 100 * (tempoAtivo / tempoDiff) #Uso da CPU em porcentagem

    ociosidade = 100 * (idleDiff / tempoDiff) 

    return round(usoCpu, 2), round(ociosidade, 2)

def monitorarCpu():
    global uso_cpu_global

    # Chama lerUsoCpu que já inclui a pausa de 5 segundos internamente
    uso, ocioso = lerUsoCpu()

    # Protege a atualização da variável global com lock
    with lock:
        uso_cpu_global = uso
        ociosidade = ocioso

    print(f"Uso CPU atualizado: {uso_cpu_global}%")
    print(f"Ociosidade CPU: {ociosidade}%")
        #Dentro do with lock, a variável global uso_cpu_global é atualizada com segurança, 
        # para que outras threads não leiam ela enquanto está sendo modificada.

def thread_monitor():
    while True:
        monitorarCpu()

t = threading.Thread(target=thread_monitor)
t.start()
