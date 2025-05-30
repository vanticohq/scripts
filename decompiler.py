#!/usr/bin/env python3
import argparse
import json
import os
import sys
from urllib.parse import urlparse

import requests


def fetch_remote_sourcemap(uri, verify_ssl=True):
    """Faz o download do conteúdo do sourcemap remoto a partir da URL."""
    try:
        response = requests.get(uri, verify=verify_ssl)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[ERRO] Falha ao buscar sourcemap: {e}")
        return None


def save_source_files(sourcemap_content, output_directory):
    """
    Decodifica o sourcemap JSON, e salva cada fonte em sua respectiva pasta
    dentro do diretório de saída fornecido.
    """
    try:
        map_object = json.loads(sourcemap_content)
    except json.JSONDecodeError as e:
        print(f"[ERRO] Falha ao decodificar JSON: {e}")
        return

    # Verifica se contém as chaves necessárias
    if 'sources' not in map_object or 'sourcesContent' not in map_object:
        print("[ERRO] Sourcemap não contém 'sources' ou 'sourcesContent'.")
        return

    sources = map_object['sources']
    sources_content = map_object['sourcesContent']

    if len(sources) != len(sources_content):
        print("[AVISO] O número de 'sources' não corresponde ao número de 'sourcesContent'. Alguns arquivos podem não ser salvos corretamente.")

    for source, content in zip(sources, sources_content):
        # Sanitiza o caminho para remover prefixos indesejados, como "webpack:///"
        if source.startswith("webpack:///"):
            source = source.replace("webpack:///", "", 1)
        elif source.startswith("webpack://"):
            source = source.replace("webpack://", "", 1)

        # Separa o caminho e o nome do arquivo
        source = source.lstrip("/")  # Remove barras iniciais
        file_path = os.path.join(output_directory, source)

        # Cria diretórios necessários
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content if content is not None else "")
            print(f"[INFO] Arquivo salvo: {file_path}")
        except Exception as e:
            print(f"[ERRO] Falha ao salvar o arquivo {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Extrai arquivos fonte de um sourcemap remoto.")
    parser.add_argument("uri", help="URL do arquivo .js.map")
    parser.add_argument("output_directory", help="Diretório de saída para os arquivos extraídos")
    parser.add_argument("--disable-ssl-verification", action="store_true",
                        help="Desabilita a verificação SSL ao fazer requisições HTTP")
    args = parser.parse_args()

    # Verifica se o diretório de saída existe; se não, cria
    output_dir = os.path.abspath(args.output_directory)
    if not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"[ERRO] Não foi possível criar o diretório {output_dir}: {e}")
            sys.exit(1)

    # Busca o sourcemap remoto
    sourcemap_content = fetch_remote_sourcemap(args.uri, verify_ssl=not args.disable_ssl_verification)
    if sourcemap_content is None:
        sys.exit(1)

    # Salva os arquivos fonte extraídos do sourcemap
    save_source_files(sourcemap_content, output_dir)


if __name__ == "__main__":
    main()
