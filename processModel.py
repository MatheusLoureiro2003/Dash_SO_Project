import os

def processos_todos():
    """Retorna e imprime uma lista de todos os PIDs encontrados em /proc"""
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    print("PIDs encontrados:", pids)
    return pids


def read_status(pid):
    """Lê e retorna os dados do arquivo /proc/[pid]/status como dicionário, com prints de debug"""
    status_path = f'/proc/{pid}/status'
    status_info = {}

    print(f"\n📄 Lendo arquivo: {status_path}")

    try:
        with open(status_path) as f:
            for line in f:
                print(f"🔹 Linha lida: {line.strip()}")
                if ':' in line:
                    key, value = line.split(':', 1)
                    status_info[key.strip()] = value.strip()
        print(f"✅ Dicionário final para PID {pid}:")
        for k, v in status_info.items():
            print(f"   {k}: {v}")
        return status_info

    except FileNotFoundError:
        print(f"⚠️ Processo {pid} não existe mais (FileNotFoundError)")
        return None
    except PermissionError:
        print(f"⛔ Sem permissão para acessar {status_path} (PermissionError)")
        return None
