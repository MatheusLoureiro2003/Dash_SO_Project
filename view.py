import tkinter as tk
from tkinter import ttk

uso_cpu_label = None
ociosidade_label = None
memoria_label = None
processos_listbox: ttk.Treeview | None = None
recursos_listbox: ttk.Treeview | None = None
content_listbox = None    

# MARK: View de Diretõrios a partir da root
def diretoryContentView(root, directoryData, get_directory_data_callback):
    global content_listbox

    directoryWindow = tk.Toplevel(root)
    directoryWindow.title("Conteúdo do Diretório")
    directoryWindow.geometry("800x500")    

    current_directory_path = ["/"]      
    history_stack = []                   

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

    button_frame = tk.Frame(frame_content)
    button_frame.pack(anchor="ne", pady=5)

    def on_refresh():
        refreshed_data = get_directory_data_callback(current_directory_path[0])
        if refreshed_data:
            updateDirectoryContentView(refreshed_data)
        else:
            print(f"Erro ao atualizar o diretório: {current_directory_path[0]}")

    def on_back_to_previous():
        if history_stack:
            previous_path = history_stack.pop()
            current_directory_path[0] = previous_path
            prev_data = get_directory_data_callback(previous_path)
            if prev_data:
                updateDirectoryContentView(prev_data)
            else:
                print(f"Erro ao voltar para: {previous_path}")
        else:
            print("Nenhum diretório anterior no histórico.")

    refreshButton = tk.Button(
        button_frame, text="Atualizar",
        command=on_refresh,
        bg="#b0e0e6", fg="#000000"
    )
    refreshButton.pack(side="left", padx=10)

    backPrevButton = tk.Button(
        button_frame, text="Voltar para o anterior",
        command=on_back_to_previous,
        bg="#f0e68c", fg="#000000"
    )
    backPrevButton.pack(side="left", padx=10)

    def on_item_click(event):
        selected_item = content_listbox.selection()
        if selected_item:
            item_data = content_listbox.item(selected_item, "values")
            item_path = item_data[1]
            if item_data[5] == "Diretório": 
                new_directory_data = get_directory_data_callback(item_path)
                if new_directory_data:
                    history_stack.append(current_directory_path[0])
                    current_directory_path[0] = item_path 
                    updateDirectoryContentView(new_directory_data)
                else:
                    print(f"Erro ao acessar o diretório: {item_path}")
                    updateDirectoryContentView(None) 
            else:
                print(f"Item selecionado não é um diretório: {item_data[0]}")

    content_listbox.bind("<Double-1>", on_item_click)

    updateDirectoryContentView(directoryData)

def _preparar_recursos_treeview(parent):
    """Cria Treeview para detalhar recursos abertos de um processo, agora com coluna PID."""
    cols = (
        "pid", "fd", "tipo", "caminho", "inode", "modo", "tamanho",
        "protocolo", "local_address", "remote_address", "state"
    )
    tv = ttk.Treeview(parent, columns=cols, show="headings")
    headers = {
        "pid": "PID", "fd": "FD", "tipo": "Tipo", "caminho": "Caminho",
        "inode": "Inode", "modo": "Modo", "tamanho": "Tamanho",
        "protocolo": "Protocolo", "local_address": "Local", "remote_address": "Remoto", "state": "Estado"
    }
    widths = {
        "pid": 60, "fd": 40, "tipo": 120, "caminho": 300,
        "inode": 80, "modo": 80, "tamanho": 80,
        "protocolo": 80, "local_address": 140, "remote_address": 140, "state": 100
    }
    for c in cols:
        tv.heading(c, text=headers[c])
        tv.column(c, anchor="w", width=widths[c], stretch=True)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    return tv

# MARK: Popular recursos abertos de TODOS os processos
def _popular_recursos(all_procs_data: dict): 
    """Preenche recursos_listbox com recursos combinados de TODOS os processos."""
    global recursos_listbox
    if recursos_listbox is None or not recursos_listbox.winfo_exists():
        return

    recursos_listbox.delete(*recursos_listbox.get_children())

    all_combined_resources = []
    for pid_str, proc_info in all_procs_data.items(): # Itera sobre TODOS os processos
        recursos_do_proc = proc_info.get("recursos_abertos", {})
        for categoria in (
            "arquivos_regulares", "sockets", "pipes", "dispositivos",
            "semaphores_posix", "links_quebrados_ou_inacessiveis", "outros"
        ):
            items_da_categoria = recursos_do_proc.get(categoria, [])
            for item in items_da_categoria:
                item_com_pid = item.copy()
                item_com_pid['pid'] = int(pid_str) # Adiciona o PID do processo ao recurso
                all_combined_resources.append(item_com_pid)
    
    # Opcional: Ordenar a lista global (ex: por PID, depois FD)
    try:
        all_combined_resources.sort(key=lambda x: (x.get('pid', 0), int(x.get("fd", "0")))) # '0' para fd para evitar erro se não houver
    except Exception:
        pass # Ignora erros de ordenação

    if not all_combined_resources:
        recursos_listbox.insert("", "end", values=("Sem recursos abertos no sistema.", *("",) * (len(recursos_listbox['columns']) - 1)))
        return

    for d in all_combined_resources:
        # Prepara valores para as colunas
        pid = d.get("pid", "—") # Pega o PID que foi adicionado
        fd = d.get("fd", "—")
        tipo = d.get("tipo", "—")
        caminho = d.get("caminho", "—")
        inode = d.get("inode", "—")
        modo = d.get("modo", "—")
        tamanho = d.get("tamanho", "—")
        
        # Ajuste para sockets e semáforos como na sua última versão (sem as colunas 0/1)
        protocolo_display = d.get("protocolo", "N/A")
        local_address_display = d.get("local_address", "N/A")
        remote_address_display = d.get("remote_address", "N/A")
        state_display = d.get("state", "N/A")

        if "Socket" in tipo and "Unix" in tipo:
            protocolo_display = "UNIX"
            local_address_display = d.get("caminho", "N/A")
            remote_address_display = "N/A"
            state_display = "N/A"
        elif "Semaphore" in tipo:
            protocolo_display = "N/A"
            local_address_display = "N/A"
            remote_address_display = "N/A"
            state_display = "N/A"

        recursos_listbox.insert(
            "", "end",
            values=(
                pid, # <--- AGORA USA O PID DO RECURSO COMBINADO
                fd,
                tipo,
                caminho,
                inode,
                modo,
                tamanho,
                protocolo_display,
                local_address_display,
                remote_address_display,
                state_display
            )
        )

def processView(root: tk.Tk, cpu: dict, mem: dict, procs: dict):
    """Janela que mostra lista de processos + recursos do selecionado."""
    global processos_listbox, recursos_listbox

    win = tk.Toplevel(root)
    win.title("Processos em Execução")
    win.geometry("1200x600")
    win.grab_set()

    def _on_close():
        global processos_listbox, recursos_listbox
        processos_listbox = None
        recursos_listbox = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)

    paned = ttk.Panedwindow(win, orient="vertical")
    paned.pack(fill="both", expand=True)

    # -------------- Processos (superior) ------------------------------------
    frame_top = tk.LabelFrame(paned, text="Processos", padx=10, pady=10)
    paned.add(frame_top, weight=3)

    proc_cols = (
        "pid", "usuario", "nome", "cpu", "cpu%", "threads", "total", "heap", "stack", "codigo", "paginas"
    )
    processos_listbox = ttk.Treeview(frame_top, columns=proc_cols, show="headings")
    processos_listbox.pack(fill="both", expand=True)
    for c in proc_cols:
        processos_listbox.heading(c, text=c.upper() if c != "pid" else "PID")
        processos_listbox.column(c, anchor="w", width=100 if c != "nome" else 200, stretch=True)
    # Scroll
    vsb_p = ttk.Scrollbar(frame_top, orient="vertical", command=processos_listbox.yview)
    processos_listbox.configure(yscrollcommand=vsb_p.set)
    vsb_p.pack(side="right", fill="y")

    # -------------- Recursos (inferior) -------------------------------------
    frame_bot = tk.LabelFrame(paned, text="Recursos Abertos", padx=10, pady=10) 
    paned.add(frame_bot, weight=2)
    recursos_listbox = _preparar_recursos_treeview(frame_bot)
    recursos_listbox.pack(fill="both", expand=True)
    _popular_recursos(procs) 

    atualizar_interface(cpu, mem, procs)

# MARK: View principal do dashboard
def dashboard_view(root, cpu, memoria, processos, get_directory_data_callback):
    
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

    atualizar_interface(cpu, memoria, processos)

# MARK: Atualização da interface com dados mais recentes
def atualizar_interface(cpu, memoria, processos):
    """Atualiza labels & treeviews com os dados mais recentes."""
    global uso_cpu_label, ociosidade_label, memoria_label, processos_listbox, recursos_listbox

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

   # -------- Processos (Treeview Superior) ------
    if processos_listbox is not None and processos_listbox.winfo_exists():
        processos_listbox.delete(*processos_listbox.get_children())
        if processos:
            for pid, info in processos.items():
                processos_listbox.insert(
                    "", "end",
                    values=(
                        pid,
                        info.get("usuario", "root"),
                        info.get("nome", "-"),
                        f"{info.get('tempo_total_segundos', 0)}s",
                        f"{info.get('uso_percentual_cpu', 0)}%",
                        info.get("threads", 0),
                        f"{info.get('mem_total_kb', 0)}kB",
                        f"{info.get('mem_heap_kb', 0)}kB",
                        f"{info.get('mem_stack_kb', 0)}kB",
                        f"{info.get('mem_codigo_kb', 0)}kB",
                        info.get("total_pagina", "-"),
                    ),
                    iid=str(pid)
                )
        else:
            processos_listbox.insert("", "end", values=("Sem dados", *("" for _ in range(10))))
        if processos_listbox.get_children() and not processos_listbox.selection():
            processos_listbox.selection_set(processos_listbox.get_children()[0])
            
    # -------- Recursos (Treeview Inferior) --------
    if recursos_listbox is not None and recursos_listbox.winfo_exists():
        _popular_recursos(processos) 
    else:
        recursos_listbox = None

# MARK: Atualiza a view de conteúdo do diretório
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
