# Dashboard Sistema Operacional

Este projeto é um dashboard simples para monitoramento do sistema operacional Linux, desenvolvido em Python utilizando a biblioteca Tkinter para interface gráfica. O dashboard apresenta informações sobre uso de CPU, memória e processos ativos, coletadas diretamente do sistema via `/proc`.

---

## Funcionalidades

- Monitoramento em tempo real do uso da CPU (uso e ociosidade)
- Exibição de informações globais de memória (RAM e Swap)
- Listagem detalhada dos processos ativos, incluindo uso de memória e CPU por processo
- Atualização automática dos dados a cada 5 segundos

---

## Requisitos

### Dependências do sistema (Ubuntu/Debian)

Para executar o projeto, certifique-se de ter as seguintes dependências instaladas:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk make build-essential
