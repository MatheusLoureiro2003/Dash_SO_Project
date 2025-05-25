# Nome do programa
APP = main.py

# Comando Python (use python ou python3 dependendo do seu sistema)
PYTHON = python3

# Alvo padrão
run:
	@echo "Iniciando o dashboard..."
	$(PYTHON) $(APP)

# Instalar dependências (se houver requirements.txt)
install:
	@echo "Instalando dependências..."
	$(PYTHON) -m pip install -r requirements.txt

# Limpar arquivos __pycache__ gerados
clean:
	@echo "Removendo arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -r {} +

# Atalhos de ajuda
help:
	@echo "Comandos disponíveis:"
	@echo "  make run      -> Executa o dashboard"
	@echo "  make install  -> Instala dependências (se tiver requirements.txt)"
	@echo "  make clean    -> Limpa arquivos temporários"
	@echo "  make help     -> Mostra essa ajuda"
