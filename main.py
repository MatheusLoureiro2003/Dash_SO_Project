#Projeto Dashboard Sistemas Operacionais

#Importar funçôes para dash (cpu, memoria, disco)
import time
from cpuModel import lerUsoCpu
from processModel import processos_todos

uso = lerUsoCpu()
print(f"Uso da CPU: {uso}%")
processos_todos()

