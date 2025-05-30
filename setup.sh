#!/bin/bash

echo "INICIANDO SETUP!"

if [ -d "venv" ]; then
	rm -rf venv
	echo "PASTA VENV ENCONTRADA, REMOVENDO!"
	python3 -m venv venv
	echo "AMBIENTE CRIADO!"
else
	python3 -m venv venv
	echo "AMBIENTE CRIADO!"
fi

source venv/bin/activate
echo "AMBIENTE ATIVADO!"

echo "INSTALANDO DEPENDÊNCIAS..."
pip install -r requirements.txt

echo "SETUP FINALIZADO!"
