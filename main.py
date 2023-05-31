from src.proxy import ProxyServer
from config import PROXIES
import threading

def main():
    for PROXY in PROXIES:
        if PROXY["STATUS"] == "ENABLED":
            threading.Thread(target=ProxyServer(PROXY["HOST"], PROXY["PORT"], 1024).start).start()


if __name__ == '__main__':
    main()

