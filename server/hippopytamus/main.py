import socket
from hippopytamus.protocol.interface import Protocol, Servlet

host = '127.0.0.1'
port = 8000


class TCPServer:
    def __init__(self, protocol: Protocol, service: Servlet):
        self.protocol = protocol
        self.service = service

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: timeout (maybe?)
        sock.bind((host, port))

        sock.listen()
        print(sock.getsockname())

        while True:
            connection, address = sock.accept()

            print(f"new client: {address}")
            context = {}
            while True:
                read = False
                data = b''
                while not read:
                    data += connection.recv(1024)
                    data, read = self.protocol.feed_parse(data, context)
                request = self.protocol.parse_request(data, context)
                response = self.service.process_request(request)
                result = self.protocol.prepare_response(response)
                connection.sendall(result)
                if 'keep-alive' not in context:
                    break
            connection.close()


if __name__ == "__main__":
    from hippopytamus.protocol.http import HttpProtocol10, HttpService
    protocol = HttpProtocol10()
    service = HttpService()
    server = TCPServer(protocol, service)
    server.listen()
