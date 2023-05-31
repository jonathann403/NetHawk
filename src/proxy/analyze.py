def extract_host_port(request):
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
