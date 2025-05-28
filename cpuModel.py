import time

# MARK: Função para ler o uso da CPU do sistema 

def lerUsoCpu():

    '''
     'proc' arquivos de interface do kernel
     /proc/stat arquivo com estatísticas sobre o uso da CPU
     usoCPU = 100% - tempo_ocioso / tempo_total

    '''

    with open("/proc/stat", "r") as l:
        linha = l.readline() 
        partes1 = linha.split()[1:]
        valores1 = list(map(int, partes1))
        
    time.sleep(5) #bloqueante

    with open("/proc/stat", "r") as l:
        linha = l.readline()
        partes2 = linha.split()[1:]
        valores2 = list(map(int, partes2))

    tempo1 = sum(valores1) #soma de todos os tempos registrados
    tempo2 = sum(valores2)

    tempoOcioso1 = valores1[3]
    tempoOcioso2 = valores2[3]

    tempoDiff = tempo2 - tempo1

    idleDiff = tempoOcioso2 - tempoOcioso1 ##idle -> tempo de ociosidade da CPU

    tempoAtivo = tempoDiff - idleDiff #tempo em que a CPU realmente trabalhou

    usoCpu = 100 * (tempoAtivo / tempoDiff) # Calculo de uso da CPU em porcentagem

    ociosidade = 100 * (idleDiff / tempoDiff) 

    return round(usoCpu, 2), round(ociosidade, 2)
