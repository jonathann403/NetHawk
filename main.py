from analyze import extract_host_port
from config import PROXIES
import threading
import socket


class ProxyServer:

    def __init__(self, bind_host, bind_port, buffer_size):
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.buffer_size = buffer_size

    def start(self):
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            proxy_socket.bind((self.bind_host, self.bind_port))
            proxy_socket.listen(5)
            print(f"[*] Proxy server started on {self.bind_host}:{self.bind_port}")
        except Exception as e:
            print(f"[*] Failed to start proxy server on {self.bind_host}:{self.bind_port} | {e}")
            return

        while True:
            try:
                client_socket, addr = proxy_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except Exception as e:
                print(f"[*] Failed to accept client connection | {e}")

    def handle_client(self, client_socket):
        # Receive the client's request
        request = client_socket.recv(self.buffer_size)
        # print("[*] Received request:\n", request)

        # Extract the host and port from the request headers
        host, port = extract_host_port(request)
        print(f"[*] {self.bind_host}:{self.bind_port} | Request sent to {host}:{port}")

        if port == 443:  # HTTPS connection
            self.handle_https_tunnel(self, client_socket, host, port)
        else:  # HTTP connection
            self.handle_http_request(self, client_socket, request, host, port)

    @staticmethod
    def handle_http_request(self, client_socket, request, host, port):
        # Forward the request to the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((host, port))
        target_socket.send(request)

        # Receive the response from the target server
        try:
            response = target_socket.recv(self.buffer_size)
        except Exception as e:
            print(f"[*] Failed to receive response from target server | {e}")
            return
        # print("[*] Received response:\n", response)

        # Send the response back to the client
        client_socket.send(response)

        # Close the connections
        target_socket.close()
        client_socket.close()

    @staticmethod
    def handle_https_tunnel(self, client_socket, host, port):
        # Establish a tunnel with the target server
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        target_socket.connect((host, port))

        # Send a success response to the client
        success_response = b"HTTP/1.1 200 Connection established\r\n\r\n"
        client_socket.send(success_response)

        # Start bidirectional forwarding between the client and target server
        forward_client_to_target = threading.Thread(target=self.forward_data, args=(self, client_socket, target_socket, host, port))
        forward_target_to_client = threading.Thread(target=self.forward_data, args=(self, target_socket, client_socket, host, port))

        forward_client_to_target.start()
        forward_target_to_client.start()

    @staticmethod
    def forward_data(self, source_socket, destination_socket, host, port):
        while True:
            try:
                data = source_socket.recv(self.buffer_size)
                if data:
                    destination_socket.send(data)
                else:
                    break
            except OSError as e:
                print(f"[*] {self.bind_host}:{self.bind_port} | {host}:{port} closed | {e}")
                break
        source_socket.close()
        destination_socket.close()


def main():
    for PROXY in PROXIES:
        if PROXY["STATUS"] == "ENABLED":
            threading.Thread(target=ProxyServer(PROXY["HOST"], PROXY["PORT"], 8192).start).start()


if __name__ == '__main__':
    main()

