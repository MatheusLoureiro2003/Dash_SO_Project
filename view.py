import tkinter as tk
from tkinter import ttk
#from customtkinter import CTkLabel, CTkTextbox, CTkFrame

# --- Widgets globais ----------------------------------------------------------
uso_cpu_label = None
ociosidade_label = None
memoria_label = None
processos_listbox: ttk.Treeview | None = None
recursos_listbox: ttk.Treeview | None = None
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

# =============================================================================
# 2) PROCESSOS – TREEVIEWS DE PROCESSOS E RECURSOS
# =============================================================================

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


def _popular_recursos(pid, procs_dict):
    """Preenche recursos_listbox incluindo a coluna PID."""
    global recursos_listbox
    if recursos_listbox is None or not recursos_listbox.winfo_exists():
        return
    # valida PID
    if not pid or not str(pid).isdigit() or str(pid) not in procs_dict:
        return
    recursos_listbox.delete(*recursos_listbox.get_children())
    rec = procs_dict[str(pid)]["recursos_abertos"]
    todas = []
    for cat in ("arquivos_regulares", "sockets", "pipes", "dispositivos",
                "semaphores_posix", "links_quebrados_ou_inacessiveis", "outros"):
        todas.extend(rec.get(cat, []))
    try:
        todas.sort(key=lambda x: int(x.get("fd", 0)))
    except:
        pass
    for d in todas:
        recursos_listbox.insert(
            "", "end",
            values=(
                pid,
                d.get("fd", "N/A"),
                d.get("tipo", "N/A"),
                d.get("caminho", "N/A"),
                d.get("inode", "0"),
                d.get("modo", "0"),
                d.get("tamanho", "0"),
                d.get("protocolo", "N/A"),
                d.get("local_address", "N/A"),
                d.get("remote_address", "N/A"),
                d.get("state", "N/A")
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

    def _on_select(event=None):
        sel = processos_listbox.selection()
        if sel:
            _popular_recursos(processos_listbox.item(sel[0], "values")[0], procs)

    processos_listbox.bind("<<TreeviewSelect>>", _on_select)

    atualizar_interface(cpu, mem, procs)

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

   # -------- Processos (Treeview) ------ (Treeview) ------
    if processos_listbox and processos_listbox.winfo_exists():
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
                )
        else:
            processos_listbox.insert("", "end", values=("Sem dados", *("",) * 10))

        # Seleciona primeiro processo automático se nada selecionado
        if processos_listbox.get_children() and not processos_listbox.selection():
            processos_listbox.selection_set(processos_listbox.get_children()[0])

# No atualizar_interface(cpu, mem, procs), use:

    # -------- Recursos (Treeview) --------
    if recursos_listbox and recursos_listbox.winfo_exists():
        sel = processos_listbox.selection()
        if sel:
            pid_sel = processos_listbox.item(sel[0], "values")[0]
            if pid_sel.isdigit() and pid_sel in processos:
                _popular_recursos(pid_sel, processos)
    else:
        recursos_listbox = None

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
