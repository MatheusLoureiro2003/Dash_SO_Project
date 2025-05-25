from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
import sys
import threading
import time
from PyQt5.QtWidgets import QApplication
from  cpuModel import lerUsoCpu
from memoryModel import lerUsoMemoria

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard do Sistema")
        self.layout = QVBoxLayout()

        self.label_cpu = QLabel("CPU: --%")
        self.label_mem = QLabel("Memória: --%")

        self.layout.addWidget(self.label_cpu)
        self.layout.addWidget(self.label_mem)

        self.setLayout(self.layout)

    def atualizar_cpu(self, uso_cpu):
        self.label_cpu.setText(f"CPU: {uso_cpu:.2f}%")

    def atualizar_memoria(self, uso_mem):
        self.label_mem.setText(f"Memória: {uso_mem:.2f}%")


def atualizar_periodicamente(view):
    while True:
        uso_cpu, ociosidade = lerUsoCpu()
        uso_mem, memDisponivel, memTotal, memVirtualTotal = lerUsoMemoria()
        view.atualizar_cpu(uso_cpu)
        view.atualizar_memoria(uso_mem)
        time.sleep(2)

def run():
    app = QApplication(sys.argv)
    view = DashboardView()
    view.show()

    t = threading.Thread(target=atualizar_periodicamente, args=(view,))
    t.daemon = True
    t.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()
