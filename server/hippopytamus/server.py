import socket
from hippopytamus.protocol.interface import Protocol, Servlet
import threading


class TCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host="localhost", port=8000):
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # TODO: timeout (maybe?)
        sock.bind((self.host, self.port))

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


class ThreadedTCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host="localhost", port=8000):
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen()
        print(sock.getsockname())

        while True:
            connection, address = sock.accept()
            print(f"new client: {address}")
            client = threading.Thread(
                    target=self.thread,
                    args=(connection, address,)
            )
            client.start()

    def thread(self, connection, address):
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


# this is a very naive implementation that will result in
# many unnecessary calls to read while polling each
# socket
class SimpleNonBlockingTCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host="localhost", port=8000):
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port

    def accept_connection(self, sock, connections):
        try:
            connection, address = sock.accept()
            connection.setblocking(False)
            print(f"new client: {address}")
            connections.append({
                "connection": connection,
                "address": address,
                "context": {},
                "data": b'',
                "read": False,
            })
        except BlockingIOError:
            pass

    def process(self, conn, i, to_remove):
        conn['data'], conn['read'] = self.protocol.feed_parse(
                conn['data'], conn['context'])
        if conn['read']:
            request = self.protocol.parse_request(
                    conn['data'], conn['context'])
            response = self.service.process_request(request)
            result = self.protocol.prepare_response(response)
            conn['connection'].sendall(result)
            if 'keep-alive' not in conn['context']:
                conn['connection'].close()
                to_remove.append(i)

    def read(self, conn, i, to_remove) -> bool:
        try:
            conn['data'] += conn['connection'].recv(1024)
            return True
        except BlockingIOError:
            return False
        except Exception as err:
            print(err)
            conn['connection'].close()
            to_remove.append(i)
            return False

    def clear_connections(self, connections, to_remove):
        for i in to_remove:
            if i > 0:
                connections[i] = connections.pop()  # swap remove
            else:
                connections.pop()
            continue
        to_remove.clear()

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind((self.host, self.port))

        sock.listen()
        print(sock.getsockname())
        connections = []

        to_remove = []
        while True:
            self.clear_connections(connections, to_remove)
            self.accept_connection(sock, connections)
            for i, conn in enumerate(connections):
                read = self.read(conn, i, to_remove)
                if read:
                    self.process(conn, i, to_remove)
