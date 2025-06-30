import tkinter as tk
from tkinter import ttk

# Variáveis globais para armazenar widgets
uso_cpu_label = None
ociosidade_label = None
memoria_label = None
processos_listbox = None

# Mark: Função para listar o conteúdo de um diretório específico
def diretoryContentView(root, content):
    directoryWindow = tk.Toplevel(root)
    directoryWindow.title("Conteúdo do Diretório")
    directoryWindow.geometry("800x500")

# Mark: Função para exibir a janela detalhada de processos
def processView(root, cpu, memoria, processos):
    global processos_listbox

    processos_window = tk.Toplevel(root)
    processos_window.title("Processos em Execução")
    processos_window.geometry("800x500")  

    frame_proc = tk.LabelFrame(processos_window, text="Processos", padx=10, pady=10)
    frame_proc.pack(fill="both", expand=True, padx=10, pady=5)

    colunas = ("pid", "usuario", "nome", "cpu", "cpu_percent", "threads", "total", "heap", "stack", "codigo", "paginas")

    processos_listbox = ttk.Treeview(frame_proc, columns=colunas, show="headings")
    processos_listbox.pack(fill="both", expand=True)

    processos_listbox.heading("pid", text="PID")
    processos_listbox.heading("usuario", text="Usuário")
    processos_listbox.heading("nome", text="Nome")
    processos_listbox.heading("cpu", text="CPU time")
    processos_listbox.heading("cpu_percent", text="CPU%")
    processos_listbox.heading("threads", text="Threads")
    processos_listbox.heading("total", text="Mem Total")
    processos_listbox.heading("heap", text="Heap")
    processos_listbox.heading("stack", text="Stack")
    processos_listbox.heading("codigo", text="Código")
    processos_listbox.heading("paginas", text="Páginas")

    for coluna in colunas:
        processos_listbox.column(coluna, anchor="w", width=100, stretch=True)

    atualizar_interface(cpu, memoria, processos)

#MARK: Função para criar a interface do dashboard
def dashboard_view(root, cpu, memoria, processos):
    for widget in root.winfo_children():
        widget.destroy()

    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox

    root.title("Dashboard do Sistema Operacional")
    root.geometry("900x600")

    # Frame Opçoes
    frame_opcoes = tk.LabelFrame(root, text="Opções", padx=10, pady=10)
    frame_opcoes.pack(fill="x", padx=10, pady=5)

    # Botoes Opcoes
    processButton = tk.Button(frame_opcoes, text="Processos", 
                              command=lambda: processView(root, cpu, memoria, processos))
    processButton.pack(side="left", padx=5, pady=5)
    directoryButton = tk.Button(frame_opcoes, text="Diretório", 
                                command=lambda: diretoryContentView(root, "/"))  # Passa o diretório raiz como exemplo
    directoryButton.pack(side="left", padx=5, pady=5)

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
    memoria_label = tk.Label(frame_mem, text="Informações de Memória", anchor="w", justify="left")  
    memoria_label.pack(anchor="w")

    # Por isso, garantimos que a variável global 'processos_listbox' seja None aqui,
    # para que 'atualizar_interface' saiba que não deve tentar manipulá-la.
    processos_listbox = None 

    atualizar_interface(cpu, memoria, processos)

#MARK: Função para atualizar a interface com os dados mais recentes
def atualizar_interface(cpu, memoria, processos):
    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox

    if uso_cpu_label and ociosidade_label: 
        if cpu:
            uso_cpu_label.config(
                text=f"Uso da CPU: {cpu.get('uso_cpu', 'N/A')}%     |    "
                    f"Total de Processos: {cpu.get('total_processos', 'N/A')}"
            )
            ociosidade_label.config(
                text=f"Tempo Ocioso: {cpu.get('ocioso', 'N/A')}%     |   "
                    f"Total de Threads: {cpu.get('total_threads', 'N/A')}"
            )
        else:
            uso_cpu_label.config(text="Uso da CPU: Calculando...")
            ociosidade_label.config(text="Tempo Ocioso: Calculando...")

    if memoria_label:
        if memoria:
            # Formata os dados de memória em uma string multilinha
            texto_mem = "\n".join([f"{chave}: {valor}" for chave, valor in memoria.items()])
        else:
            texto_mem = "Sem dados de memória ainda"
        memoria_label.config(text=texto_mem) 
    
    
    if processos_listbox is not None: 
        for item in processos_listbox.get_children():
            processos_listbox.delete(item)

        # Insere os novos dados dos processos na Treeview
        if processos:
            for pid, info in processos.items():
                nome = info.get("nome", "Desconhecido")
                usuario = info.get("usuario", "root")
                cpu_proc = f"{info.get('tempo_total_segundos', 'N/A')}s"
                cpu_percent = f"{info.get('uso_percentual_cpu', 0)}%"
                threads = f"{info.get('threads', 0)}"
                mem_total = f"{info.get('mem_total_kb', 'N/A')}kB"
                mem_heap = f"{info.get('mem_heap_kb', 'N/A')}kB"
                mem_stack = f"{info.get('mem_stack_kb', 'N/A')}kB"
                mem_codigo = f"{info.get('mem_codigo_kb', 'N/A')}kB"
                paginas = info.get("total_pagina", "N/A")

                processos_listbox.insert(
                    "", "end", values=(
                        pid, usuario, nome, cpu_proc, cpu_percent, threads,
                        mem_total, mem_heap, mem_stack, mem_codigo, paginas
                    )
                )
        else:
            # Se não houver dados de processos, insere uma linha indicando
            processos_listbox.insert("", "end", values=("Sem dados", "", "", "", "", "", "", "", "", "", ""))