# uso da memoria global
# uso da memoria por processo
# Função que pega as informções da memória no /proc/meminfo
# calcular a porcentagem do uso de memória


# PERCENTUAL DE USO DE MEMORIA

def lerUsoMemoria():
    with open("/proc/meminfo") as l:
        for linha in l:
            print(linha.strip())
            linha = l.readlines()
            memTotal = int(linha[0].split()[1])
            memDisponivel = int(linha[2].split()[1]) # memória que pode ser usada sem trocar dados para o disco

        # MemTotal:        8129200 kB.     linha 0. (RAM)
        # MemFree:          227316 kB.     linha 1
        #MemAvailable:     5528300 kB.     linha 2

        memVirtualTotal = int(linha[14].split()[1])
        memVirtualLivre = int(linha[15].split()[1])
        #SwapTotal:       2097148 kB
        #SwapFree:        2097148 kB

        if memVirtualTotal > 0:
            usoMemVirtual = 100 * (1 - memVirtualLivre / memVirtualTotal)
        else:
            usoMemVirtual = 0 

        memTotal_MB = memTotal
        memVirtualTotal_MB = memVirtualTotal

        usoMemoria = 100 * (1 - memDisponivel / memTotal)

        return round(usoMemoria,2), memDisponivel , memTotal_MB, memVirtualTotal_MB



## TESTE

# usoRAM, memDisponivelKB, memTotalMB, memVirtualTotalMB = lerUsoMemoria()

# memDisponivelMB = memDisponivelKB

# print("========== DASHBOARD DE MEMÓRIA ==========")
# print(f"Uso de RAM:               {usoRAM:.2f} %")
# print(f"Memória Disponível:       {memDisponivelMB:.2f} kb")
# print(f"Memória RAM Total:        {memTotalMB:.2f} kb")
# print(f"Memória Virtual (Swap):   {memVirtualTotalMB:.2f} kb")
# print("==========================================")
