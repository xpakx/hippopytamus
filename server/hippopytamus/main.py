if __name__ == "__main__":
    from hippopytamus.protocol.http import HttpProtocol10, HttpService
    from hippopytamus.server import ThreadedTCPServer
    protocol = HttpProtocol10()
    service = HttpService()
    server = ThreadedTCPServer(protocol, service)
    server.listen()
