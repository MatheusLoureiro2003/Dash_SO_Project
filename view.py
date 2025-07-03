import tkinter as tk
from tkinter import ttk

"""view.py ‒ GUI do dashboard
--------------------------------------------------------------
Mostra métricas globais (CPU/Memória), lista de processos e,
para o processo selecionado, os recursos de arquivo/sockets/etc.
Estrutura principal:
    ▸ dashboard_view(root, cpu, mem, procs)
    ▸ processView(...)  (janela secundária)
    ▸ diretoryContentView(...)  (janela secundária)
As duas Treeviews (processos / recursos) são mantidas em
variáveis globais para serem atualizadas por atualizar_interface().
"""

# ----------------------------------------------------------------------------
# Objetos de gráfico (placeholder – não usados ainda)
# ----------------------------------------------------------------------------
cpu_fig = cpu_ax = mem_fig = mem_ax = cpu_canvas = mem_canvas = None

# ----------------------------------------------------------------------------
# Widgets globais (referências para atualização periódica)
# ----------------------------------------------------------------------------
uso_cpu_label: tk.Label | None = None
ociosidade_label: tk.Label | None = None
memoria_label: tk.Label | None = None
processos_listbox: ttk.Treeview | None = None
recursos_listbox: ttk.Treeview | None = None
content_listbox: ttk.Treeview | None = None

# =============================================================================
# 1) DIRETÓRIO – VIEW E ATUALIZAÇÃO
# =============================================================================

def updateDirectoryContentView(items: list[dict] | None):
    """Preenche a content_listbox com *items* – lista de dicionários."""
    global content_listbox
    if content_listbox is None or not content_listbox.winfo_exists():
        return

    content_listbox.delete(*content_listbox.get_children())

    if not items:
        content_listbox.insert("", "end", values=("Sem dados", *("",) * 6))
        return

    for it in items:
        content_listbox.insert(
            "", "end",
            values=(
                it.get("Nome", "—"),
                it.get("Caminho", "—"),
                it.get("Permissões", "—"),
                it.get("Data de Criação", "—"),
                it.get("Data de Modificação", "—"),
                it.get("Tipo", "—"),
                it.get("Tamanho", "—"),
            ),
        )


def diretoryContentView(root: tk.Tk, directory_items: list[dict] | None):
    """Abre janela modal com conteúdo de diretório."""
    global content_listbox

    win = tk.Toplevel(root)
    win.title("Conteúdo do Diretório")
    win.geometry("800x500")
    win.grab_set()  # modal simples

    def _on_close():
        global content_listbox
        content_listbox = None
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", _on_close)

    frame = tk.LabelFrame(win, text="Conteúdo", padx=10, pady=10)
    frame.pack(fill="both", expand=True, padx=10, pady=5)

    cols = ("Nome", "Caminho", "Permissões", "Data de Criação", "Data de Modificação", "Tipo", "Tamanho")
    content_listbox = ttk.Treeview(frame, columns=cols, show="headings")
    content_listbox.pack(fill="both", expand=True)
    for c in cols:
        content_listbox.heading(c, text=c)
        content_listbox.column(c, anchor="w", width=120, stretch=True)

    updateDirectoryContentView(directory_items)

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

# =============================================================================
# 3) DASHBOARD PRINCIPAL
# =============================================================================

def dashboard_view(root: tk.Tk, cpu: dict, mem: dict, procs: dict):
    """Constrói/atualiza a janela principal do dashboard."""
    # Remove widgets antigos antes de redesenhar
    for w in root.winfo_children():
        w.destroy()

    global uso_cpu_label, ociosidade_label, memoria_label
    global processos_listbox, recursos_listbox

    root.title("Dashboard do Sistema Operacional")
    root.geometry("900x600")

    # ------------------ Frame Opções ------------------
    f_opt = tk.LabelFrame(root, text="Opções", padx=10, pady=10)
    f_opt.pack(fill="x", padx=10, pady=5)

    tk.Button(
        f_opt,
        text="Processos",
        command=lambda: processView(root, cpu, mem, procs),
    ).pack(side="left", padx=5)

    tk.Button(
        f_opt,
        text="Diretório",
        command=lambda: diretoryContentView(root, "/"),
    ).pack(side="left", padx=5)

    # ------------------ CPU ---------------------------
    f_cpu = tk.LabelFrame(root, text="Uso da CPU", padx=10, pady=10)
    f_cpu.pack(fill="x", padx=10, pady=5)

    uso_cpu_label = tk.Label(f_cpu, text="Uso da CPU:")
    uso_cpu_label.pack(anchor="w")
    ociosidade_label = tk.Label(f_cpu, text="Tempo Ocioso:")
    ociosidade_label.pack(anchor="w")

    # ------------------ Memória -----------------------
    f_mem = tk.LabelFrame(root, text="Uso da Memória", padx=10, pady=10)
    f_mem.pack(fill="x", padx=10, pady=5)

    memoria_label = tk.Label(f_mem, text="Informações de Memória", anchor="w", justify="left")
    memoria_label.pack(anchor="w")

    # Placeholder para futuros gráficos ----------------
    tk.Label(root, text="(Gráficos viriam aqui)").pack(expand=True)

    # Reseta ponteiros de Treeviews (serão criados em processView)
    processos_listbox = None
    recursos_listbox = None

    # Preenche imediatamente as labels de CPU/Memória
    atualizar_interface(cpu, mem, procs)

# =============================================================================
# 4) ATUALIZAÇÃO PERIÓDICA DE DADOS NO DASHBOARD
# =============================================================================

def atualizar_interface(cpu: dict, mem: dict, procs: dict):
    """Atualiza labels de CPU/Memória e, se abertos, Treeviews."""
    global uso_cpu_label, ociosidade_label, memoria_label
    global processos_listbox, recursos_listbox

    # -------- CPU --------
    if uso_cpu_label and ociosidade_label:
        if cpu:
            uso_cpu_label.config(
                text=(
                    f"Uso da CPU: {cpu.get('uso_cpu', 'N/A')}% | "
                    f"Total Processos: {cpu.get('total_processos', 'N/A')}"
                )
            )
            ociosidade_label.config(
                text=(
                    f"Tempo Ocioso: {cpu.get('ocioso', 'N/A')}% | "
                    f"Total Threads: {cpu.get('total_threads', 'N/A')}"
                )
            )
        else:
            uso_cpu_label.config(text="Uso da CPU: Calculando…")
            ociosidade_label.config(text="Tempo Ocioso: Calculando…")

        # -------- Memória ----
    if memoria_label:
        memoria_label.config(
            text="\n".join(f"{k}: {v}" for k, v in mem.items()) if mem else "Sem dados de memória ainda"
        )


    # -------- Processos (Treeview) ------ (Treeview) ------
    if processos_listbox and processos_listbox.winfo_exists():
        processos_listbox.delete(*processos_listbox.get_children())

        if procs:
            for pid, info in procs.items():
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
            if pid_sel.isdigit() and pid_sel in procs:
                _popular_recursos(pid_sel, procs)
    else:
        recursos_listbox = None