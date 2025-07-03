import os
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor

MAX_WORKERS = 10

def baixar_arquivo(base_url, destino, caminho_relativo):
    url_completo = urljoin(base_url, caminho_relativo)
    destino_arquivo = os.path.join(destino, caminho_relativo)

    os.makedirs(os.path.dirname(destino_arquivo), exist_ok=True)

    try:
        with requests.get(url_completo, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(destino_arquivo, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"[✓] Baixado: {url_completo}")
    except Exception as e:
        print(f"[ERRO] {url_completo}: {e}")

def explorar_e_baixar(base_url, destino_base, caminho_relativo="", executor=None):
    url_atual = urljoin(base_url, caminho_relativo)
    print(f"[LISTANDO] {url_atual}")

    destino_dir = os.path.join(destino_base, caminho_relativo)
    os.makedirs(destino_dir, exist_ok=True)

    try:
        resposta = requests.get(url_atual, timeout=10)
        resposta.raise_for_status()
    except Exception as e:
        print(f"[ERRO] {url_atual}: {e}")
        return

    soup = BeautifulSoup(resposta.text, 'html.parser')
    links = soup.find_all('a')

    for link in links:
        href = link.get('href')
        if not href or href.startswith('?') or href.startswith('/') or href in ('../', '/'):
            continue

        novo_caminho = os.path.join(caminho_relativo, href)
        if href.endswith('/'):
            # Diretório: entrar recursivamente
            explorar_e_baixar(base_url, destino_base, novo_caminho, executor)
        else:
            # Arquivo: baixar já
            if executor:
                executor.submit(baixar_arquivo, base_url, destino_base, novo_caminho)
            else:
                baixar_arquivo(base_url, destino_base, novo_caminho)

def main():
    parser = argparse.ArgumentParser(description='Download recursivo direto com progresso.')
    parser.add_argument('url', help='URL da página "Index of"')
    parser.add_argument('-o', '--output', default='downloads', help='Diretório de saída')
    parser.add_argument('-t', '--threads', type=int, default=MAX_WORKERS, help='Número de threads simultâneas')
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        explorar_e_baixar(args.url, args.output, executor=executor)

if __name__ == '__main__':
    main()
