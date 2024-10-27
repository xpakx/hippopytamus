if __name__ == "__main__":
    from hippopytamus.protocol.http import HttpProtocol10, HttpService
    from hippopytamus.server.nonblocking import PollTCPServer
    host = '192.168.50.212'
    port = 8000
    protocol = HttpProtocol10()
    service = HttpService()
    server = PollTCPServer(protocol, service, host, port)
    server.listen()
