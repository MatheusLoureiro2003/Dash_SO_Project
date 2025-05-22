import os

def processos_todos():
    """Retorna e imprime uma lista de todos os PIDs encontrados em /proc"""
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    print("PIDs encontrados:", pids)
    return pids