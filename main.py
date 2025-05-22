#Projeto Dashboard Sistemas Operacionais

#Importar funçôes para dash (cpu, memoria, disco)
import time
from dashController import update_dashboard
# from cpuModel import lerUsoCpu, lerOciosidadeCpu 

#from processModel import processos_todos, read_status

#pids = processos_todos()
#if pids:
#        read_status(pids[0])
# uso = lerUsoCpu()
# ociosidade = lerOciosidadeCpu()
# print(f"Utilização CPU: {uso}%")
# print(f"Tempo Ocioso CPU {ociosidade}%")
# processos_todos()

def main():
    while True:
        update_dashboard()
        time.sleep(1)

if __name__ == "__main__":
    main()
