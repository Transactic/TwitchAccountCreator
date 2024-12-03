from typing import List, Dict
import requests, random, string, time, json, threading, traceback, re
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from ssl import create_default_context
from twocaptcha import TwoCaptcha

# Config loading
try:
    with open("./config/config.json", "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise FileNotFoundError("Configuration file not found at './config/config.json'")
except json.JSONDecodeError:
    raise ValueError("Invalid JSON format in the configuration file")

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
used_proxies = []

# ANSI color codes for console output
class Color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET_ALL = "\033[0m"


# Function Definitions
def get_proxy() -> Dict[str, str]:
    try:
        with open('./assets/proxies.txt', encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            raise ValueError("Proxy list is empty")

        chosen_proxy = random.choice(lines)
        if config['proxyType'] == "socks5":
            return {'http': f'socks5://{chosen_proxy}', 'https': f'socks5://{chosen_proxy}'}
        elif config['proxyType'] in ["http/https", "http"]:
            return {"http": f"http://{chosen_proxy}", "https": f"https://{chosen_proxy}"}
        else:
            raise ValueError(f"Unsupported proxy type: {config['proxyType']}")
    except Exception as e:
        print(f"{Color.RED}Error getting proxy: {e}{Color.RESET_ALL}")
        return {}


def write_to_file(file: str, text: str):
    try:
        with open(file, "a+", encoding="utf-8") as f:
            f.write(text)
    except IOError as e:
        print(f"{Color.RED}Error writing to file {file}: {e}{Color.RESET_ALL}")


def generate_password() -> str:
    characters = string.ascii_letters + string.punctuation + string.digits
    return "".join(random.choice(characters) for _ in range(random.randint(8, 16)))


def generate_birthday() -> Dict[str, int]:
    return {
        "day": random.randint(1, 28),
        "month": random.randint(1, 12),
        "year": random.randint(1980, 2002)
    }


def random_string(length: int) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


def random_username() -> str:
    try:
        with open("./assets/usernames.txt", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return random.choice(lines) if lines else f"User{random.randint(1000, 9999)}"
    except FileNotFoundError:
        return f"User{random.randint(1000, 9999)}"


def solve_captcha(session: requests.Session, count: int) -> str:
    print(f"{Color.YELLOW}[{count}] Waiting for captcha to be resolved...{Color.RESET_ALL}")
    try:
        solver = TwoCaptcha(config['2capthcaKey'])
        result = solver.funcaptcha(
            sitekey="E5554D43-23CC-1982-971D-6A2262A2CA24",
            url="https://www.twitch.tv/",
            version="v3",
            score=0.1
        )
        print(f"{Color.GREEN}[{count}] Captcha solved successfully!{Color.RESET_ALL}")
        return result.get("code", "")
    except Exception as e:
        print(f"{Color.RED}Captcha solving failed: {e}{Color.RESET_ALL}")
        return ""


class TwitchAccountGenerator:
    def __init__(self, proxy: Dict[str, str], count: int):
        self.proxy = proxy
        self.count = count
        self.session = requests.Session()
        if config.get("useProxy"):
            self.session.proxies.update(proxy)
        self.session.headers.update({"User-Agent": random_string(10)})

    def register(self):
        try:
            # Generate email
            email = f"user{random.randint(1000, 9999)}@gmail.com"  # Replace with dynamic email fetching
            payload = {
                "username": random_username() + random_string(4),
                "password": generate_password(),
                "email": email,
                "birthday": generate_birthday(),
                "client_id": "kimne78kx3ncx6brgo4mv6wki5h1ko",
                "include_verification_code": True,
                "arkose": {"token": solve_captcha(self.session, self.count)}
            }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": self.session.headers["User-Agent"]
            }
            response = self.session.post("https://passport.twitch.tv/register", json=payload, headers=headers)
            if response.status_code == 200 and "access_token" in response.json():
                token = response.json()["access_token"]
                print(f"{Color.GREEN}Account created! Username: {payload['username']}, Token: {token}{Color.RESET_ALL}")
                write_to_file("./out/tokens.txt", f"{token}\n")
            else:
                print(f"{Color.RED}Failed to create account: {response.text}{Color.RESET_ALL}")
        except Exception as e:
            print(f"{Color.RED}Error during registration: {e}{Color.RESET_ALL}")


def main():
    threads = config.get("threading", 5)
    accounts_to_create = config.get("Number_of_accounts_to_be_created", 10)

    for i in range(accounts_to_create):
        proxy = get_proxy()
        generator = TwitchAccountGenerator(proxy, i + 1)
        threading.Thread(target=generator.register).start()


if __name__ == "__main__":
    main()
