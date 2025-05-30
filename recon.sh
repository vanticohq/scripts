#!/bin/bash

# Recon master script - Atualizado com theHarvester
clear
echo "==============================="
echo "🔥 RECON MASTER 🔥"
echo "==============================="
echo ""

# ▶️ Checando dependências
tools=(gau waybackurls katana gf httpx nuclei ffuf)
for tool in "${tools[@]}"; do
  if ! command -v $tool &> /dev/null; then
    echo "[!] Ferramenta '$tool' não encontrada. Instale antes de continuar."
    exit 1
  fi
done

# 🎯 Solicita o domínio
read -p "[+] Digite o domínio alvo (ex: exemplo.com ou site.com.br): " DOMINIO

# Remove 'https://', 'http://' e o TLD completo (com ou sem ponto final)
DOMINIO_SEM_PROTOCOL=$(echo $DOMINIO | sed -E 's/^https?:\/\///')
DOMINIO_SEM_TLD=$(echo $DOMINIO_SEM_PROTOCOL | sed -E 's/\.[a-z]+$//')

# Cria a pasta com o nome do domínio sem protocolo e TLD
mkdir -p busca/$DOMINIO_SEM_TLD
cd busca/$DOMINIO_SEM_TLD || exit


# 🧩 Função de coleta de URLs
function coleta_urls() {
  echo "[*] Coletando com gau, waybackurls e katana..."
  echo $DOMINIO | waybackurls > wayback.txt
  gau $DOMINIO > gau.txt
  katana -u https://$DOMINIO -silent > katana.txt
  cat wayback.txt gau.txt katana.txt | sort -u > all_urls.txt
  cat all_urls.txt | grep "=" > urls_com_param.txt
  echo "[+] URLs totais com parâmetros: $(wc -l < urls_com_param.txt)"
}

# Função de filtro
function filtro_gf() {
  if [[ ! -f urls_com_param.txt ]]; then
    echo "[!] Arquivo 'urls_com_param.txt' não encontrado. Rode a opção 1 primeiro."
    return
  fi

  echo "[*] Filtrando com gf (incluindo patterns avançados)..."

  patterns=(xss potential_xss xss-params sqli lfi ssrf rce redirect ssti interestingparams debug_logic idor)

  for tipo in "${patterns[@]}"; do
    if [[ -f ~/.gf/$tipo.json ]]; then
      cat urls_com_param.txt | gf $tipo | sort -u > "${tipo}_urls.txt"
      num_linhas=$(wc -l < "${tipo}_urls.txt")
      
      if [[ $num_linhas -eq 0 ]]; then
        rm -f "${tipo}_urls.txt"
        echo "[*] Nenhum resultado para $tipo — arquivo não criado."
      else
        echo "[+] Possíveis $tipo encontrados: $num_linhas"
      fi
    else
      echo "[!] Pattern '$tipo' não encontrado em ~/.gf — pulei esse."
    fi
  done
}


#Função de verificação com httpx
function verificar_httpx() {
  echo "[*] Verificando quais URLs estão ativas..."
  cat urls_com_param.txt | httpx -silent -sc -title -td > alive_urls.txt
  echo "[+] URLs ativas: $(wc -l < alive_urls.txt)"
}

# ⚡ Função de scan com nuclei
function rodar_nuclei() {
  echo "[*] Rodando nuclei nas URLs ativas..."
  nuclei -l alive_urls.txt -silent -o nuclei_resultados.txt
  echo "[+] Resultados salvos em nuclei_resultados.txt"
}

# 💥 Função de fuzzing com ffuf (XSS)
function fuzzar_xss() {
  read -p "[*] Digite uma URL alvo com FUZZ no parâmetro (ex: https://site.com/search?q=FUZZ): " alvo
  read -p "[*] Caminho da wordlist de XSS (ex: payloads.txt): " wordlist
  ffuf -u "$alvo" -w "$wordlist" -fs 0 -mc 200,302 -t 50 | tee ffuf_xss_resultados.txt
  echo "[+] Resultados salvos em ffuf_xss_resultados.txt"
}

# 🧩 Função para mostrar o menu
function show_menu() {
  echo ""
  echo "=== Selecione as etapas que deseja executar ==="
  echo "1) Coletar URLs com gau + waybackurls + katana"
  echo "2) Filtrar parâmetros e usar gf (XSS, LFI, etc)"
  echo "3) Verificar URLs ativas com httpx"
  echo "4) Rodar nuclei (CVE scan)"
  echo "5) Rodar fuzzing básico de XSS com ffuf"
  echo "0) Sair"
  echo "=============================================="
}

# 🧩 Loop de escolha de opções
while true; do
  show_menu
  read -p "[*] Escolha uma opção (0 para sair): " opcao

  case $opcao in

    1) coleta_urls ;;
    2) filtro_gf ;;
    3) verificar_httpx ;;
    4) rodar_nuclei ;;
    5) fuzzar_xss ;;
    0) 
      echo "[+] Saindo do script. Até a próxima!" 
      exit 0
      ;;
    *) 
      echo "[!] Opção inválida, tente novamente."
      ;;
  esac
done
