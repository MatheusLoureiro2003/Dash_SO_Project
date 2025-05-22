from cpuModel import lerOciosidadeCpu, lerUsoCpu
from processModel import processos_todos
from terminalView import render_dashboard

def update_dashboard():
    cpu = lerUsoCpu()
    processos = processos_todos()
    render_dashboard(cpu, processos)
