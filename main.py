#Projeto Dashboard Sistemas Operacionais

#Importar funçôes para dash (cpu, memoria, disco)
import time
from cpuModel import lerUsoCpu, lerOciosidadeCpu 

from processModel import processos_todos

uso = lerUsoCpu()
ociosidade = lerOciosidadeCpu()
print(f"Utilização CPU: {uso}%")
print(f"Tempo Ocioso CPU {ociosidade}%")
processos_todos()

