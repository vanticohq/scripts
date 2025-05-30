#!/bin/bash

# Caminho para o arquivo de IDs
ID_FILE="/home/treino/ferramentas/ids.txt"
OUTPUT_FILE="resultados_positivos.txt"

# Verifica se foi fornecido pelo menos um IP
if [ -z "$1" ]; then
    echo "Uso: $0 <IP1[,IP2,IP3,...]>"
    exit 1
fi

# Separa os IPs em um array
IFS=',' read -r -a TARGET_IPS <<< "$1"

# Verifica se o arquivo de IDs existe
if [ ! -f "$ID_FILE" ]; then
    echo "Arquivo de IDs não encontrado: $ID_FILE"
    exit 1
fi

# Conta total de IDs para exibir progresso
TOTAL_IDS=$(wc -l < "$ID_FILE")
echo "Total de IDs a testar: $TOTAL_IDS"
echo "IPs alvo: ${TARGET_IPS[*]}"
echo "---------------------------------------------"
sleep 1

# Limpa arquivo de saída
> "$OUTPUT_FILE"

# Inicializa contador
COUNT=0

# Loop pelos IPs
for TARGET_IP in "${TARGET_IPS[@]}"; do
    echo ">> Testando IDs no IP: $TARGET_IP"
    echo "---------------------------------------------"

    while IFS= read -r ID; do
        COUNT=$((COUNT + 1))

        # Exibe barra de progresso simples
        echo -ne "[$COUNT/$TOTAL_IDS] Testando ID: $ID\r"

        RESULT=$( (echo "Found ID: $ID" && ike-scan -M -A -n "$ID" "$TARGET_IP") 2>/dev/null | grep -B14 "1 returned handshake" | grep "Found ID:" )

        if [ -n "$RESULT" ]; then
            echo -e "\n[+] Handshake encontrado com ID: $ID no IP $TARGET_IP"
            echo "ID: $ID | IP: $TARGET_IP" >> "$OUTPUT_FILE"
        fi

    done < "$ID_FILE"

    echo -e "\nFinalizado para IP: $TARGET_IP"
    echo "---------------------------------------------"
done

echo -e "\n✅ Varredura finalizada!"
echo "Resultados salvos em: $OUTPUT_FILE"
