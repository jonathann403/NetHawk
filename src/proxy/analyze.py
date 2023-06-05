DEFAULT_PORT = 80

def extract_host_port(request_headers):
    host = ""
    port = DEFAULT_PORT

    for header in request_headers:
        if header.startswith(b'Host:'):
            host_with_port = header.split(b' ')[1].decode()
            if ':' in host_with_port:
                host, port_str = host_with_port.split(':')
                try:
                    port = int(port_str)
                except ValueError:
                    pass  # Invalid port, use the default
            else:
                host = host_with_port
            break

    return host, port
