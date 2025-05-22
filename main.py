#Projeto Dashboard Sistemas Operacionais

#Importar funçôes para dash (cpu, memoria, disco)
import time
from cpuModel import lerUsoCpu

uso = lerUsoCpu()
print(f"Uso da CPU: {uso}%")

