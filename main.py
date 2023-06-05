from src.proxy import ProxyServer
from config import PROXIES
import threading
from concurrent.futures import ThreadPoolExecutor

def start_proxy(proxy):
    ProxyServer(proxy["HOST"], proxy["PORT"], 1024).start()

def main():
    enabled_proxies = [proxy for proxy in PROXIES if proxy["STATUS"] == "ENABLED"]
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(start_proxy, enabled_proxies)

if __name__ == '__main__':
    main()
