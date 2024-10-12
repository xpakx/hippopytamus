import socket


host = '127.0.0.1'
port = 8000


class TCPServer:
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
            connection.sendall(data)
            connection.close()


if __name__ == "__main__":
    server = TCPServer()
    server.listen()
