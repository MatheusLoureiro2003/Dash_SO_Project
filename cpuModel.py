"""
    Ler dados sobre o uso da CPU
    retornar valor em porcentagem
    """
import time

def lerUsoCpu():
    
    #
    #proc arquivos de interface do kernel
    #/proc/stat arquivo com estatísticas sobre o uso da CPU
    # usoCPU = 100% - tempo_ocioso / tempo_total

    with open("/proc/stat", "r") as f:
        linha = f.readline() #le a primeira linha
        partes1 = linha.split()[1:]
        valores1 = list(map(int, partes1))
        
    time.sleep(5)

    with open("/proc/stat", "r") as f:
        linha = f.readline()
        partes2 = linha.split()[1:]
        valores2 = list(map(int, partes2))

    tempo1 = sum(valores1) #soma de todos os tempos registrados
    tempo2 = sum(valores2)

    #idle -> tempo de ociosidade da CPU
    idle1 = valores1[3]
    idle2 = valores2[3]

    tempoDiff = tempo2 - tempo1
    idleDiff = idle2 - idle1
    ociosidade = tempoDiff - idleDiff
    usoCpu = 100 * (ociosidade / tempoDiff)

    return round(usoCpu, 2)
   