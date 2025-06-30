import os
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def baixar_arquivos_index(base_url, destino, caminho_relativo=""):
    url_atual = urljoin(base_url, caminho_relativo)
    print(f"Acessando: {url_atual}")

    try:
        resposta = requests.get(url_atual)
        resposta.raise_for_status()
    except Exception as e:
        print(f"Erro ao acessar {url_atual}: {e}")
        return

    soup = BeautifulSoup(resposta.text, 'html.parser')
    links = soup.find_all('a')

    for link in links:
        href = link.get('href')
        if not href or href.startswith('?') or href.startswith('/'):
            continue
        if href in ('../', '/'):
            continue

        novo_caminho_relativo = os.path.join(caminho_relativo, href)
        url_completo = urljoin(base_url, novo_caminho_relativo)

        if href.endswith('/'):
            # Diretório: chamada recursiva
            baixar_arquivos_index(base_url, destino, novo_caminho_relativo)
        else:
            destino_arquivo = os.path.join(destino, novo_caminho_relativo)
            os.makedirs(os.path.dirname(destino_arquivo), exist_ok=True)
            print(f"Baixando: {url_completo} → {destino_arquivo}")
            try:
                with requests.get(url_completo, stream=True) as r:
                    r.raise_for_status()
                    with open(destino_arquivo, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            except Exception as e:
                print(f"Erro ao baixar {url_completo}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Baixar arquivos de uma página "Index of", preservando estrutura de diretórios.')
    parser.add_argument('url', help='URL da página "Index of" (ex: http://exemplo.com/arquivos/)')
    parser.add_argument('-o', '--output', default='downloads', help='Diretório de saída (padrão: downloads)')
    args = parser.parse_args()

    baixar_arquivos_index(args.url, args.output)

if __name__ == '__main__':
    main()