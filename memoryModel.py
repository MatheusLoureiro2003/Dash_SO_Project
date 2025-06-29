# MARK: RETORNA INFORMAÇOES SOBRE O USO DE MEMORIA

def lerUsoMemoria():

    with open("/proc/meminfo") as l:
        
        linha = l.readlines()
        
        memTotal = int(linha[0].split()[1])
        memDisponivel = int(linha[2].split()[1]) 
        # memória que pode ser usada sem trocar dados para o disco

        memVirtualTotal = int(linha[14].split()[1]) #SwapTotal: 097148 kB
        memVirtualLivre = int(linha[15].split()[1])  

        if memVirtualTotal > 0:
         usoMemVirtual = 100 * (1 - memVirtualLivre / memVirtualTotal)
         usoMemVirtual = 100 * (1 - memVirtualLivre / memVirtualTotal)
        else:
         usoMemVirtual = 0 
         usoMemVirtual = 0 

        usoMemoria = 100 * (1 - memDisponivel / memTotal)

        return {
            "Uso Memória RAM (%)": round(usoMemoria, 2),
            "Memória RAM Disponível (kB)": memDisponivel,
            "Memória RAM Total (kB)": memTotal,
            "Swap Total (kB)": memVirtualTotal,
            "Swap Livre (kB)": memVirtualLivre,
            "Uso Swap (%)": round(usoMemVirtual, 2)
        }
