import tkinter as tk

# Variáveis globais para armazenar widgets
uso_cpu_label = None
ociosidade_label = None
memoria_label = None
processos_listbox = None


def dashboard_view(root, cpu, memoria, processos):
    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox

    root.title("Dashboard do Sistema Operacional")
    root.geometry("700x500")

    # Frame CPU
    frame_cpu = tk.LabelFrame(root, text="Uso da CPU", padx=10, pady=10)
    frame_cpu.pack(fill="x", padx=10, pady=5)

    uso_cpu_label = tk.Label(frame_cpu, text="Uso da CPU: ")
    uso_cpu_label.pack(anchor="w")

    ociosidade_label = tk.Label(frame_cpu, text="Tempo Ocioso: ")
    ociosidade_label.pack(anchor="w")

    # Frame Memória
    frame_mem = tk.LabelFrame(root, text="Uso da Memória", padx=10, pady=10)
    frame_mem.pack(fill="x", padx=10, pady=5)

    memoria_label = tk.Label(frame_mem, text="Informações de Memória")
    memoria_label.pack(anchor="w")

    # Frame Processos
    frame_proc = tk.LabelFrame(root, text="Processos", padx=10, pady=10)
    frame_proc.pack(fill="both", expand=True, padx=10, pady=5)

    processos_listbox = tk.Listbox(frame_proc)
    processos_listbox.pack(fill="both", expand=True)

    # Primeira atualização
    atualizar_interface(cpu, memoria, processos)


def atualizar_interface(cpu, memoria, processos):
    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox

    if cpu:
        uso_cpu_label.config(text=f"Uso da CPU: {cpu.get('uso_cpu_percent', 0)}%")
        ociosidade_label.config(text=f"Tempo Ocioso: {cpu.get('ociosidade_percent', 0)}%")
    else:
        uso_cpu_label.config(text="Uso da CPU: Carregando...")
        ociosidade_label.config(text="Tempo Ocioso: Carregando...")

    if memoria:
        texto_mem = "\n".join([f"{chave}: {valor}" for chave, valor in memoria.items()])
    else:
        texto_mem = "Sem dados de memória ainda"
    memoria_label.config(text=texto_mem)

    processos_listbox.delete(0, tk.END)
    if processos:
        for pid, info in processos.items():
            nome = info.get("nome", "Desconhecido")
            usuario = info.get("usuario", "root")
            cpu_proc = info.get("tempo_total_segundos", "N/A")
            processos_listbox.insert(tk.END, f"PID: {pid} | Usuário: {usuario} | Nome: {nome} | CPU: {cpu_proc}%")
    else:
        processos_listbox.insert(tk.END, "Sem dados de processos ainda")
