"""
    Ler dados sobre o uso da CPU
    retornar valor em porcentagem
    """
    
def lerUsoCpu():
    
    with open("/proc/stat", "r") as f:
        linha = f.readline() 
   