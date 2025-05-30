import subprocess
import argparse

# Define ANSI color codes for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
ENDC = "\033[0m"

def colorize(text, is_secure):
    """Wrap the text with appropriate color codes."""
    return f"{GREEN}{text}{ENDC}" if is_secure else f"{RED}{text}{ENDC}"

def check_spf_record(record):
    """Analyze the SPF record to check for vulnerabilities."""
    if not record:
        return ("No SPF record found.", False)

    if "v=spf1" in record:
        # Check for mechanisms that allow sending
        if "all" in record:
            if "-all" in record:
                return ("SPF record is secure (-all detected).", True)
            elif "~all" in record:
                return ("SPF record is neutral (~all detected), which may lead to softfail.", False)
            else:
                return ("SPF record is too permissive (allowing all), which is insecure.", False)
        else:
            return ("SPF record does not explicitly allow or deny sending, which may be insecure.", False)
    else:
        return ("Invalid SPF record format detected.", False)

def check_dmarc_record(record):
    """Analyze the DMARC record to check for vulnerabilities."""
    if not record:
        return ("No DMARC record found.", False)

    if "v=DMARC1" in record:
        # Check for policy that allows no action
        if "p=none" in record:
            return ("DMARC policy is set to none, which does not prevent spoofing.", False)
        elif "p=quarantine" in record or "p=reject" in record:
            return ("DMARC policy is strong (quarantine or reject).", True)
        else:
            return ("DMARC record has an unrecognized policy.", False)
    else:
        return ("Invalid DMARC record format detected.", False)

def check_spf(domain):
    """Check the SPF record for a domain using the dig command."""
    result = subprocess.run(["dig", "+short", "TXT", domain], stdout=subprocess.PIPE, text=True)
    records = result.stdout.strip().split("\n")
    for record in records:
        if "v=spf1" in record:
            return record.strip('"')
    return None

def check_dmarc(domain):
    """Check the DMARC record for a domain using the dig command."""
    result = subprocess.run(["dig", "+short", "TXT", f"_dmarc.{domain}"], stdout=subprocess.PIPE, text=True)
    records = result.stdout.strip().split("\n")
    for record in records:
        if "v=DMARC1" in record:
            return record.strip('"')
    return None

def main():
    parser = argparse.ArgumentParser(description="Check and analyze SPF and DMARC records of a domain.")
    parser.add_argument("-d", "--domain", type=str, help="The domain to check.")
    parser.add_argument("-l", "--list", type=str, help="A file containing a list of domains to check.")
    args = parser.parse_args()

    if args.domain:
        domains = [args.domain]
    elif args.list:
        try:
            with open(args.list, 'r') as file:
                domains = file.read().splitlines()
        except FileNotFoundError:
            print(colorize(f"The file {args.list} was not found.", False))
            return
    else:
        print(colorize("No domain or list provided.", False))
        return

    for domain in domains:
        spf_record = check_spf(domain)
        dmarc_record = check_dmarc(domain)
        spf_analysis, spf_secure = check_spf_record(spf_record)
        dmarc_analysis, dmarc_secure = check_dmarc_record(dmarc_record)

        # Print organized information with color
        print(f"Domain: {domain}")
        print(f"SPF Record: {colorize(spf_record if spf_record else 'None', spf_secure)}")
        print(f"  Analysis: {colorize(spf_analysis, spf_secure)}")
        print(f"  Vulnerable: {colorize('Yes' if not spf_secure else 'No', spf_secure)}")
        print(f"DMARC Record: {colorize(dmarc_record if dmarc_record else 'None', dmarc_secure)}")
        print(f"  Analysis: {colorize(dmarc_analysis, dmarc_secure)}")
        print(f"  Vulnerable: {colorize('Yes' if not dmarc_secure else 'No', dmarc_secure)}\n")

if __name__ == "__main__":
    main()
