#!/bin/bash

check_ip() {
    proxychains curl -s https://check.torproject.org/api/ip | grep -oP '"IP":"\K[^"]+'
}

while true; do
    OLD_IP=$(check_ip)
    echo "IP atual: $OLD_IP"

    {
        echo 'authenticate "tor777"'
        echo 'signal newnym'
        echo 'quit'
    } | nc -q 1 127.0.0.1 9051

    echo "[$(TZ="America/Sao_Paulo" date '+%Y-%m-%d %H:%M:%S')] Novo IP requisitado via Tor!"

    sleep 5  # espera 5 segundos para novo circuito formar

    NEW_IP=$(check_ip)
    echo "Novo IP: $NEW_IP"

    if [[ "$OLD_IP" == "$NEW_IP" ]]; then
        echo "ATENÇÃO: IP não mudou! Tentando novamente em breve..."
    fi

    sleep 60  # espera 5 minutos antes da próxima troca
done
