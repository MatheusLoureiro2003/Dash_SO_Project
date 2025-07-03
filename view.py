import tkinter as tk
from tkinter import ttk
from customtkinter import CTkLabel, CTkTextbox, CTkFrame
#versao thayssa
# --- Widgets globais ----------------------------------------------------------
uso_cpu_label = None
ociosidade_label = None
memoria_label = None
processos_listbox = None  # Treeview da janela de processos
content_listbox = None    # Treeview da janela de diretório

# -----------------------------------------------------------------------------
# View: Conteúdo de diretório
# -----------------------------------------------------------------------------

def diretoryContentView(root, directoryData, get_directory_data_callback):
    """Abre uma Toplevel com o conteúdo de um diretório."""
    global content_listbox

    directoryWindow = tk.Toplevel(root)
    directoryWindow.title("Conteúdo do Diretório")
    directoryWindow.geometry("800x500")    
     

    # Callback para soltar o ponteiro global quando a janela for fechada
    def _on_close():
        global content_listbox
        content_listbox = None
        directoryWindow.destroy()

    directoryWindow.protocol("WM_DELETE_WINDOW", _on_close)

    frame_content = tk.LabelFrame(directoryWindow, text="Conteúdo do Diretório", padx=10, pady=10)
    frame_content.pack(fill="both", expand=True, padx=10, pady=5)
    
    columns = (
        "Nome", "Caminho", "Permissões", "Data de Criação",
        "Data de Modificação", "Tipo", "Tamanho Bytes"
    )
    content_listbox = ttk.Treeview(frame_content, columns=columns, show="headings")
    content_listbox.pack(fill="both", expand=True)

    for col in columns:
        content_listbox.heading(col, text=col)

    backButton = tk.Button(
        frame_content, text="Voltar",
        command=directoryWindow.destroy,
        bg="#d0d0d0", fg="#000000"
    )
    backButton.pack(side="top", anchor="ne", padx=10, pady=10)

    #pra cada linha, ao clicar, abre os subdiretórios
    def on_item_click(event):
        selected_item = content_listbox.selection()
        if selected_item:
            item_data = content_listbox.item(selected_item, "values")
            item_path = item_data[1]
            if item_data[5] == "Diretório": 
                new_directory_data = get_directory_data_callback(item_path)
                if new_directory_data:
                    updateDirectoryContentView(new_directory_data)
                else:
                    print(f"Erro ao acessar o diretório: {item_path}")
                    updateDirectoryContentView(None) 
            else:

                print(f"Item selecionado não é um diretório: {item_data[0]}")
    content_listbox.bind("<Double-1>", on_item_click)
    # Chama a função que popula a Treeview
    updateDirectoryContentView(directoryData)

# -----------------------------------------------------------------------------
# View: Processos
# -----------------------------------------------------------------------------

def processView(root, cpu, memoria, processos):
    """Abre uma Toplevel com a lista de processos."""
    global processos_listbox

    processos_window = tk.Toplevel(root)
    processos_window.title("Processos em Execução")
    processos_window.geometry("800x500")

    # ❶ Callback para soltar o ponteiro global quando a janela for fechada
    def _on_close():
        global processos_listbox
        processos_listbox = None
        processos_window.destroy()

    processos_window.protocol("WM_DELETE_WINDOW", _on_close)

    frame_proc = tk.LabelFrame(processos_window, text="Processos", padx=10, pady=10)
    frame_proc.pack(fill="both", expand=True, padx=10, pady=5)

    colunas = (
        "pid", "usuario", "nome", "cpu", "cpu_percent", "threads",
        "total", "heap", "stack", "codigo", "paginas"
    )
    processos_listbox = ttk.Treeview(frame_proc, columns=colunas, show="headings")
    processos_listbox.pack(fill="both", expand=True)

    for coluna in colunas:
        processos_listbox.heading(coluna, text=coluna.upper() if coluna != "pid" else "PID")
        processos_listbox.column(coluna, anchor="w", width=100, stretch=True)

    # Preenche imediatamente com os dados atuais
    atualizar_interface(cpu, memoria, processos)

# -----------------------------------------------------------------------------
# Dashboard principal
# -----------------------------------------------------------------------------

def dashboard_view(root, cpu, memoria, processos, get_directory_data_callback):
    """Cria a interface principal do dashboard."""
    # Limpa widgets antigos
    for widget in root.winfo_children():
        widget.destroy()

    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox

    root.title("Dashboard do Sistema Operacional")
    root.geometry("900x400")

    # --- Frame de opções ------------------------------------------------------
    frame_opcoes = tk.LabelFrame(root, text="Opções", padx=10, pady=10)
    frame_opcoes.pack(fill="x", padx=10, pady=5)

    processButton = tk.Button(
        frame_opcoes, text="Processos",
        command=lambda: processView(root, cpu, memoria, processos)
    )
    processButton.pack(side="left", padx=5, pady=5)

    directoryButton = tk.Button(
        frame_opcoes, text="Diretório",
        command=lambda: diretoryContentView(root, get_directory_data_callback("/"), get_directory_data_callback)  # Chama a função de callback para obter o conteúdo do diretório
    )
    directoryButton.pack(side="left", padx=5, pady=5)

    # --- Frame CPU -----------------------------------------------------------
    frame_cpu = tk.LabelFrame(root, text="Uso da CPU", padx=10, pady=10)
    frame_cpu.pack(fill="x", padx=10, pady=5)

    uso_cpu_label = tk.Label(frame_cpu, text="Uso da CPU: ")
    uso_cpu_label.pack(anchor="w")

    ociosidade_label = tk.Label(frame_cpu, text="Tempo Ocioso: ")
    ociosidade_label.pack(anchor="w")

    # --- Frame Memória -------------------------------------------------------
    frame_mem = tk.LabelFrame(root, text="Uso da Memória", padx=10, pady=10)
    frame_mem.pack(fill="x", padx=10, pady=5)

    memoria_label = tk.Label(
        frame_mem, text="Informações de Memória", anchor="w", justify="left"
    )
    memoria_label.pack(anchor="w")
    
    # Garante que o ponteiro global aponta para None até a janela de processos abrir
    processos_listbox = None

    # Rende r os valores iniciais
    atualizar_interface(cpu, memoria, processos)

# -----------------------------------------------------------------------------
# Atualização da interface (executada pelo controller a cada segundo)
# -----------------------------------------------------------------------------

def atualizar_interface(cpu, memoria, processos):
    """Atualiza labels & treeviews com os dados mais recentes."""
    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox

    # --- CPU -----------------------------------------------------------------
    if uso_cpu_label and ociosidade_label:
        if cpu:
            uso_cpu_label.config(
                text=(
                    f"Uso da CPU: {cpu.get('uso_cpu', 'N/A')}%     |    "
                    f"Total de Processos: {cpu.get('total_processos', 'N/A')}"
                )
            )
            ociosidade_label.config(
                text=(
                    f"Tempo Ocioso: {cpu.get('ocioso', 'N/A')}%     |   "
                    f"Total de Threads: {cpu.get('total_threads', 'N/A')}"
                )
            )
        else:
            uso_cpu_label.config(text="Uso da CPU: Calculando…")
            ociosidade_label.config(text="Tempo Ocioso: Calculando…")

    # --- Memória -------------------------------------------------------------
    if memoria_label:
        texto_mem = (
            "\n".join(f"{k}: {v}" for k, v in memoria.items())
            if memoria else "Sem dados de memória ainda"
        )
        memoria_label.config(text=texto_mem)

    # --- Processos -----------------------------------------------------------
    if processos_listbox is not None:
        # ❷ Se a janela foi fechada, winfo_exists() devolve 0
        if not processos_listbox.winfo_exists():
            processos_listbox = None
        else:
            # Limpa linhas antigas
            for item in processos_listbox.get_children():
                processos_listbox.delete(item)

            if processos:
                for pid, info in processos.items():
                    processos_listbox.insert(
                        "", "end",
                        values=(
                            pid,
                            info.get("usuario", "root"),
                            info.get("nome", "Desconhecido"),
                            f"{info.get('tempo_total_segundos', 'N/A')}s",
                            f"{info.get('uso_percentual_cpu', 0)}%",
                            info.get("threads", 0),
                            f"{info.get('mem_total_kb', 'N/A')}kB",
                            f"{info.get('mem_heap_kb', 'N/A')}kB",
                            f"{info.get('mem_stack_kb', 'N/A')}kB",
                            f"{info.get('mem_codigo_kb', 'N/A')}kB",
                            info.get("total_pagina", "N/A"),
                        ),
                    )
            else:
                processos_listbox.insert(
                    "", "end", values=("Sem dados", *("" for _ in range(10)))
                )

# -----------------------------------------------------------------------------
# Atualização da TreeView de diretório
# -----------------------------------------------------------------------------

def updateDirectoryContentView(content):
    global content_listbox

    # ❷ Evita atualização se a janela já foi fechada
    if content_listbox is None or not content_listbox.winfo_exists():
        content_listbox = None
        return

    # Limpa linhas antigas
    for item in content_listbox.get_children():
        content_listbox.delete(item)

    if content and isinstance(content, list):
        for info in content:
          if isinstance(info, dict):
            content_listbox.insert(
                "", "end",
                values=(
                    info.get("Nome", "Desconhecido"),
                    info.get("Caminho", "/"),
                    info.get("Permissões", "N/A"),
                    info.get("Data de Criação", "N/A"),
                    info.get("Data de Modificação", "N/A"),
                    info.get("Tipo", "N/A"),
                    info.get("Tamanho (Bytes)", "0"),
                ),
            )
        else:
            content_listbox.insert(
                "", "end", values=("Sem dados", *("" for _ in range(6)))
            )
    else:
        content_listbox.insert(
            "", "end", values=("Sem dados", *("" for _ in range(6)))
        )
