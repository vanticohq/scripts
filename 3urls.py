#!/usr/bin/env python3
"""
extract_urls_and_secrets.py ― Extrai URLs e segredos (API keys, tokens,
Authorization Bearer/Basic, JWTs) de:

* Arquivos locais (.js, .txt, etc.);
* Uma única URL (ex.: https://example.com/app.js);
* Um arquivo .txt contendo uma lista de URLs (uma por linha).

Uso:
    python extract_urls_and_secrets.py alvo1 [alvo2 ...] [-o file] [-os file]

Onde “alvo” pode ser:
    • Caminho para um arquivo local a ser analisado;
    • Uma URL iniciando com http:// ou https://;
    • Um arquivo .txt cujas linhas sejam URLs.

Exemplos:
    # Analisa um JS remoto
    python extract_urls_and_secrets.py https://example.com/app.js

    # Analisa diversos alvos, inclusive lista de URLs
    python extract_urls_and_secrets.py local.js urls.txt https://foo.com/bar.js -o urls.csv -os secrets.tsv
"""

import argparse
import pathlib
import re
import sys
import urllib.request
from collections import OrderedDict
from typing import Dict, Iterable, List, Set, Tuple

# ---------------------------------------------------------------------------
# 1) URLs
# ---------------------------------------------------------------------------

URL_RE = re.compile(
    r'''(?xi)
    (?:
        (?P<proto>https?|ftp)://[^\s'"<>]+
        |
        # Caminhos relativos/absolutos a partir do domínio raiz
        (?<![A-Za-z0-9])/(?:
            [\w./-]+
            (?:
                \?
                [^\s'"<>]*
            )?
        )
    )
    '''
)

# ---------------------------------------------------------------------------
# 2) Segredos
# ---------------------------------------------------------------------------

SECRET_PATTERNS: Dict[str, str] = OrderedDict(
    {
        "Authorization Bearer": r"Bearer\s+[A-Za-z0-9\-_.=]+",
        "Authorization Basic": r"Basic\s+[A-Za-z0-9=+/]+",
        "JWT": r"ey[Jj][A-Za-z0-9\-_=]+?\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*",
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
        "Heroku API Key": r"(?<![A-Za-z0-9])[a-f0-9]{32}(?![A-Za-z0-9])",
        "Generic Secret": r'(?i)(api|secret|token|key)[=:\\"\' ]+[A-Za-z0-9\-_.]{10,}',
    }
)

SECRET_RES = {k: re.compile(v) for k, v in SECRET_PATTERNS.items()}


# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------


def fetch_url(url: str) -> str:
    """Baixa o conteúdo de uma URL e devolve str (utf‑8)."""
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="ignore")
    except Exception as e:
        sys.exit(f"Erro baixando {url}: {e}")


def extract_urls(text: str) -> List[str]:
    """Extrai URLs únicas preservando ordem."""
    seen: Set[str] = set()
    out: List[str] = []
    for m in URL_RE.finditer(text):
        url = m.group(0)
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def extract_secrets(text: str) -> List[Tuple[str, str]]:
    """Extrai pares (tipo, valor) preservando ordem."""
    found: List[Tuple[str, str]] = []
    for t, rx in SECRET_RES.items():
        for m in rx.finditer(text):
            found.append((t, m.group(0)))
    return found


def iter_targets(targets: Iterable[str]) -> Iterable[Tuple[str, str]]:
    """
    Itera sobre cada alvo, devolvendo tuplas (descrição, conteúdo).
    A descrição é usada para mensagens; o conteúdo, para análise.
    """
    for target in targets:
        # URL?
        if re.match(r"^https?://", target, flags=re.I):
            yield target, fetch_url(target)
            continue

        path = pathlib.Path(target)
        if not path.exists():
            sys.exit(f"Alvo '{target}' não existe e não é URL válida.")

        # Arquivo .txt só com URLs?
        if path.suffix.lower() == ".txt":
            try:
                for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    ln = ln.strip()
                    if ln and re.match(r"^https?://", ln, flags=re.I):
                        yield ln, fetch_url(ln)
            except Exception as e:
                sys.exit(f"Erro lendo {path}: {e}")
        else:
            try:
                yield str(path), path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                sys.exit(f"Erro lendo {path}: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Extrai URLs e segredos de arquivos, URLs ou listas de URLs."
    )
    ap.add_argument(
        "targets",
        nargs="+",
        help="Arquivo(s), URL(s) ou .txt com linhas de URLs a processar",
    )
    ap.add_argument("-o", "--out-urls", type=pathlib.Path, help="Saída só de URLs")
    ap.add_argument(
        "-os", "--out-secrets", type=pathlib.Path, help="Saída só de segredos"
    )
    args = ap.parse_args()

    all_urls: List[str] = []
    all_secrets: List[Tuple[str, str]] = []

    for desc, content in iter_targets(args.targets):
        print(f"--- Analisando {desc} ---")
        urls = extract_urls(content)
        secrets = extract_secrets(content)
        print(f"  {len(urls):4d} URL(s) encontradas; {len(secrets):3d} segredo(s).")
        all_urls.extend(urls)
        all_secrets.extend(secrets)

    # Deduplicação mantendo ordem
    all_urls = list(dict.fromkeys(all_urls))
    all_secrets = list(OrderedDict(((t, v), None) for t, v in all_secrets).keys())

    # ---------- URLs ----------
    if args.out_urls:
        args.out_urls.write_text("\n".join(all_urls), encoding="utf-8")  # \n = quebra de linha
        print(f"{len(all_urls)} URL(s) gravadas em {args.out_urls}")
    else:
        print("\n=== URLs ===")
        print("\n".join(all_urls))
        print(f"Total: {len(all_urls)}")

    # ---------- Segredos ----------
    if args.out_secrets:
        args.out_secrets.write_text(
            "\n".join(f"{t}\t{v}" for t, v in all_secrets), encoding="utf-8"
        )
        print(f"{len(all_secrets)} segredo(s) gravados em {args.out_secrets}")
    else:
        print("\n=== Segredos ===")
        for t, v in all_secrets:
            masked = v if t.startswith("Authorization") else v[:6] + "..." + v[-4:]
            print(f"[{t}] {masked}")
        print(f"Total: {len(all_secrets)}")


if __name__ == "__main__":
    main()
