#!/bin/bash

read -p "Digite o nome do domínio: " domain

read -p "Digite o nome do arquivo de saída: " saida

echo "Realizando busca no crt.sh"
echo "Aguarde..."

curl -s "https://crt.sh/?q=%25.${domain}&output=json" | jq -r '.[].name_value' | sort -u > $saida.txt

echo "Busca realizada, o valor total de subdomínios encontrados foi: "
wc -l $saida.txt
