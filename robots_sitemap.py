import requests
import concurrent.futures

def fetch_url(url):
    # Tenta a versão https
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"[+] {url} encontrado ({len(response.text)} bytes)"
        elif response.status_code == 403:
            return f"[-] {url} bloqueado (403 Forbidden)"
        else:
            return f"[-] {url} não encontrado ({response.status_code})"
    except requests.RequestException:
        # Se falhar, tenta com http
        url_http = url.replace("https://", "http://")
        try:
            response = requests.get(url_http, timeout=5)
            if response.status_code == 200:
                return f"[+] {url_http} encontrado ({len(response.text)} bytes)"
            elif response.status_code == 403:
                return f"[-] {url_http} bloqueado (403 Forbidden)"
            else:
                return f"[-] {url_http} não encontrado ({response.status_code})"
        except requests.RequestException:
            return f"[-] {url_http} erro ao conectar"

def scan_subdomains(subdomains):
    urls = []
    for subdomain in subdomains:
        urls.append(f"https://{subdomain}/robots.txt")
        urls.append(f"https://{subdomain}/sitemap.xml")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_url, urls)
    
    for result in results:
        print(result)

def load_subdomains():
    filename = "alvos.txt"  # Defina aqui o nome do arquivo
    try:
        with open(filename, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Erro: Arquivo '{filename}' não encontrado.")
        return []

if __name__ == "__main__":
    subdomains = load_subdomains()
    if subdomains:
        scan_subdomains(subdomains)
