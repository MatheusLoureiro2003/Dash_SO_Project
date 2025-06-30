import os

# Mark: Obtem informaçoes de uso de espaço para um dado diretorio
def getUsagePartition(diretctory):
    try:
        statsInfo = os.statvfs(diretctory)

        totalBytes = statsInfo.f_blocks * statsInfo.f_bsize
        freeBytes = statsInfo.f_bfree * statsInfo.f_bsize
        totalAvailableBytes = statsInfo.f_bavail * statsInfo.f_bsize
        usedBytes = totalBytes - freeBytes
        percentUsed = (usedBytes / totalBytes) * 100

        return{
            "Tamanho Total (Gb)": round(totalBytes / (1024 ** 3), 2),
            "Espaço Usado (Mb)": round(usedBytes / (1024 ** 2), 2),
            "Espaço Livre (Gb)": round(freeBytes / (1024 ** 3), 2),
            "Espaço Disponível (Gb)": round(totalAvailableBytes / (1024 ** 3), 2),
            "Percentual de Uso (%)": round(percentUsed, 2)  
        }
    except Exception as e:
        print(f"Erro: O diretório '{diretctory}' não foi encontrado.")
        return None    


# Mark: Funçao para leitura de arquivos
def getFileSystem ():

    partitions = []
    
    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                print(line.strip())  
                parts = line.split()
                partitions.append({
                    "Dispositivo de Bloco": parts[0],
                    "Diretorio": parts[1],
                    "Opçoes de Montagem": parts[3]
                })

                usage = getUsagePartition(parts[1])
                if usage:
                    details = {
                        "Tamanho Total (Gb)": usage["Tamanho Total (Gb)"],
                        "Espaço Usado (Mb)": usage["Espaço Usado (Mb)"],
                        "Espaço Livre (Gb)": usage["Espaço Livre (Gb)"],
                        "Espaço Disponível (Gb)": usage["Espaço Disponível (Gb)"],
                        "Percentual de Uso (%)": usage["Percentual de Uso (%)"]
                    }
                    usage.update(details)
                    partitions.append(usage)
    except FileNotFoundError:
        print("Erro: O arquivo /proc/mounts não foi encontrado.")
        return None
    return partitions

#a = getFileSystem()
#for i in a:
#    for key, value in i.items():
#        print(f"{key}: {value}")
#    print()  