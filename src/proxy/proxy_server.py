import logging
import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from src.proxy.analyze import extract_host_port

logger = logging.getLogger(__name__)

class ProxyServer:
    def __init__(self, bind_host, bind_port, buffer_size):
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.buffer_size = buffer_size
        self.shutdown_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=10)

    def start(self):
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            proxy_socket.bind((self.bind_host, self.bind_port))
            proxy_socket.listen(5)
            logger.info(f"Proxy server started on {self.bind_host}:{self.bind_port}")
        except Exception as e:
            logger.error(f"Failed to start proxy server on {self.bind_host}:{self.bind_port} | {e}")
            return

        try:
            while not self.shutdown_event.is_set():
                client_socket, addr = proxy_socket.accept()
                self.executor.submit(self.handle_client, client_socket)
        except Exception as e:
            logger.error(f"Failed to accept client connection | {e}")
        finally:
            proxy_socket.close()
            self.executor.shutdown(wait=True)

    def handle_client(self, client_socket):
        with client_socket:
            try:
                request = client_socket.recv(self.buffer_size)
                host, port = extract_host_port(request)
                logger.info(f"{self.bind_host}:{self.bind_port} | Request sent to {host}:{port}")

                if port == 443:  # HTTPS connection
                    self.handle_https_tunnel(client_socket, host, port)
                else:  # HTTP connection
                    self.handle_http_request(client_socket, request, host, port)
            except Exception as e:
                logger.error(f"Error handling client connection | {e}")

    @staticmethod
    def handle_http_request(client_socket, request, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as target_socket:
            try:
                target_socket.connect((host, port))
                target_socket.send(request)

                response = target_socket.recv(buffer_size)
                client_socket.send(response)
            except Exception as e:
                logger.error(f"Failed to handle HTTP request | {e}")

    @staticmethod
    def handle_https_tunnel(client_socket, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as target_socket:
            try:
                target_socket.connect((host, port))
                success_response = b"HTTP/1.1 200 Connection established\r\n\r\n"
                client_socket.send(success_response)

                forward_client_to_target = threading.Thread(target=ProxyServer.forward_data, args=(client_socket, target_socket))
                forward_target_to_client = threading.Thread(target=ProxyServer.forward_data, args=(target_socket, client_socket))

                forward_client_to_target.start()
                forward_target_to_client.start()
            except Exception as e:
                logger.error(f"Failed to handle HTTPS tunnel | {e}")

    @staticmethod
    def forward_data(source_socket, destination_socket):
        while True:
            try:
                data = source_socket.recv(buffer_size)
                if data:
                    destination_socket.send(data)
                else:
                    break
            except Exception as e:
                logger.error(f"Error forwarding data | {e}")
                break
