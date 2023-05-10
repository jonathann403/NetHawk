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
        proxy_socket.bind((self.bind_host, self.bind_port))
        proxy_socket.listen(5)
        print("[*] Proxy server started on {}:{}".format(self.bind_host, self.bind_port))

        while True:
            client_socket, addr = proxy_socket.accept()
            # print("[*] Accepted connection from {}:{}".format(addr[0], addr[1]))

            # Create a new thread to handle the client connection
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()

    @staticmethod
    def extract_host_port(self, request):
        host = ""
        port = 80  # Default port if not specified

        # Parse the request headers to extract the host and port
        headers = request.split(b'\r\n')
        for header in headers:
            if header.startswith(b'Host:'):
                host = header.split(b' ')[1].decode()
                if ':' in host:
                    host, port = host.split(':')
                    port = int(port)
                break

        return host, port

    def handle_client(self, client_socket):
        # Receive the client's request
        request = client_socket.recv(self.buffer_size)
        # print("[*] Received request:\n", request)

        # Extract the host and port from the request headers
        host, port = self.extract_host_port(self, request)
        print(f"[*] Request sent to {host}:{port}")

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
        response = target_socket.recv(self.buffer_size)
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
        forward_client_to_target = threading.Thread(target=self.forward_data, args=(self, client_socket, target_socket))
        forward_target_to_client = threading.Thread(target=self.forward_data, args=(self, target_socket, client_socket))

        forward_client_to_target.start()
        forward_target_to_client.start()

    @staticmethod
    def forward_data(self, source_socket, destination_socket):
        while True:
            try:
                data = source_socket.recv(self.buffer_size)
                if data:
                    destination_socket.send(data)
                else:
                    break
            except OSError as e:
                print("Error occurred during data forwarding:", e)
                break

        source_socket.close()
        destination_socket.close()


def main():
    proxy_servers = []

    for PROXY in PROXIES:
        if PROXY["STATUS"] == "ENABLED":
            proxy_servers.append(ProxyServer(PROXY["HOST"], PROXY["PORT"], 8192))

    for proxy_server in proxy_servers:
        try:
            proxy_thread = threading.Thread(target=proxy_server.start)
            proxy_thread.start()
        except OSError as e:
            print(f"[*] Proxy server on {proxy_server.bind_host}:{proxy_server.bind_port} failed to start | {e}")


if __name__ == '__main__':
    main()

