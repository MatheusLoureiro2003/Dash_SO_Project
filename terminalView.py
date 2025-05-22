def render_dashboard(cpu, processo):
    print("=" * 40)

    print(" DASHBOARD DO SISTEMA ".center(40, "="))
    print(f"CPU: {cpu:.2f}%")
    print(f"Processos: {len(processo)}")
    print("=" * 40)

