if __name__ == "__main__":
    from hippopytamus.protocol.http import HttpProtocol10, HttpService
    from hippopytamus.server import TCPServer
    protocol = HttpProtocol10()
    service = HttpService()
    server = TCPServer(protocol, service)
    server.listen()
