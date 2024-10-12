import socket


host = '127.0.0.1'
port = 8000


class TCPServer:
    def __init__(self, protocol):
        self.protocol = protocol

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
            data = connection.recv(1024)  # TODO: protocol should decide
            result = self.protocol.process_request(data)
            connection.sendall(result)
            connection.close()


class EchoProtocol:
    def process_request(self, request: bytes):
        return request


if __name__ == "__main__":
    protocol = EchoProtocol()
    server = TCPServer(protocol)
    server.listen()
