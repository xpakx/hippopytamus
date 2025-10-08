import socket
from hippopytamus.protocol.interface import Protocol, Servlet
from hippopytamus.logger.logger import LoggerFactory
import select
from typing import List, Any, Dict, Optional


# this is a very naive implementation that will result in
# many unnecessary calls to read while polling each
# socket
class SimpleNonBlockingTCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host: str = "localhost", port: int = 8000) -> None:
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port
        self.connections: List[Dict[str, Any]] = []
        self.logger = LoggerFactory.get_logger()

    def accept_connection(self, sock: socket.socket) -> None:
        try:
            connection, address = sock.accept()
            connection.setblocking(False)
            self.logger.info(f"new client: {address}")
            self.connections.append({
                "connection": connection,
                "address": address,
                "context": {},
                "data": b'',
                "read": False,
            })
        except BlockingIOError:
            pass

    def process(self, conn: Dict[str, Any], i: int, to_remove: List[int]) -> None:
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

    def read(self, conn: Dict[str, Any], i: int, to_remove: List[int]) -> bool:
        try:
            conn['data'] += conn['connection'].recv(1024)
            return True
        except BlockingIOError:
            return False
        except Exception as err:
            self.logger.warn(err)
            conn['connection'].close()
            to_remove.append(i)
            return False

    def clear_connections(self, to_remove: List[int]) -> None:
        for i in to_remove:
            if i > 0:
                self.connections[i] = self.connections.pop()  # swap remove
            else:
                self.connections.pop()
            continue
        to_remove.clear()

    def listen(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind((self.host, self.port))

        sock.listen()
        self.logger.debug(sock.getsockname())

        to_remove: List[int] = []
        while True:
            self.clear_connections(to_remove)
            self.accept_connection(sock)
            for i, conn in enumerate(self.connections):
                read = self.read(conn, i, to_remove)
                if read:
                    self.process(conn, i, to_remove)


class SelectTCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host: str = "localhost", port: int = 8000) -> None:
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port
        self.connections: List[socket.socket] = []
        self.state: List[Any] = []
        self.logger = LoggerFactory.get_logger()

    def listen(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind((self.host, self.port))

        sock.listen()
        self.logger.debug(sock.getsockname())
        self.connections.append(sock)
        self.state.append(None)

        while True:
            # TODO: use select for writing; exceptions
            readable, _, _ = select.select(self.connections, [], [])

            for conn in readable:
                if conn is sock:
                    self.accept_connection(sock)
                else:
                    index = self.connections.index(conn)
                    state = self.state[index]
                    if self.read(conn, state):
                        self.process(conn, state)

    def remove_connection(self, connection: socket.socket) -> None:
        index = self.connections.index(connection)
        self.connections.pop(index)
        self.state.pop(index)

    def accept_connection(self, sock: socket.socket) -> None:
        connection, address = sock.accept()
        connection.setblocking(False)
        self.logger.info(f"new client: {address}")
        self.connections.append(connection)
        self.state.append({
            "address": address,
            "context": {},
            "data": b'',
            "read": False,
        })

    def process(self, conn: socket.socket, state: Dict[str, Any]) -> None:
        state['data'], state['read'] = self.protocol.feed_parse(
                state['data'], state['context'])
        if state['read']:
            request = self.protocol.parse_request(
                    state['data'], state['context'])
            response = self.service.process_request(request)
            result = self.protocol.prepare_response(response)
            conn.sendall(result)
            if 'keep-alive' not in state['context']:
                conn.close()
                self.remove_connection(conn)

    def read(self, conn: socket.socket, state: Dict[str, Any]) -> bool:
        try:
            state['data'] += conn.recv(1024)
            return True
        except Exception as err:
            self.logger.warn(err)
            self.remove_connection(conn)
            return False


class PollTCPServer:
    def __init__(self, protocol: Protocol, service: Servlet,
                 host: str = "localhost", port: int = 8000) -> None:
        self.protocol = protocol
        self.service = service
        self.host = host
        self.port = port
        self.fdmap: Dict[int, Any] = {}
        self.poller: Optional[select.poll] = None
        self.logger = LoggerFactory.get_logger()

    def listen(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)
        sock.bind((self.host, self.port))

        sock.listen()
        self.logger.debug(sock.getsockname())

        self.poller = select.poll()
        self.poller.register(sock, select.POLLIN)
        self.fdmap[sock.fileno()] = {"connection": sock, "state": None}

        while True:
            events = self.poller.poll(-1)

            for fd, flag in events:
                conn = self.fdmap.get(fd)
                if not conn:
                    continue
                if conn['connection'] is sock:
                    self.accept_connection(sock)
                elif flag & select.POLLIN == select.POLLIN:
                    if self.read(conn):
                        self.process(conn)
                elif flag & select.POLLHUP != 0:
                    self.remove_connection(conn)

    def remove_connection(self, connection: Dict[str, Any]) -> None:
        fd = connection['connection'].fileno()
        self.fdmap.pop(fd)
        if not self.poller:
            return
        self.poller.unregister(fd)
        connection['connection'].close()

    def accept_connection(self, sock: socket.socket) -> None:
        connection, address = sock.accept()
        connection.setblocking(False)
        self.logger.info(f"new client: {address}")
        if not self.poller:
            return
        self.poller.register(connection, select.POLLIN)
        self.fdmap[connection.fileno()] = {
            "connection": connection,
            "address": address,
            "context": {},
            "data": b'',
            "read": False,
        }

    def process(self, conn: Dict[str, Any]) -> None:
        conn['data'], conn['read'] = self.protocol.feed_parse(
                conn['data'], conn['context'])
        if conn['read']:
            request = self.protocol.parse_request(
                    conn['data'], conn['context'])
            response = self.service.process_request(request)
            result = self.protocol.prepare_response(response)
            conn['connection'].sendall(result)
            if 'keep-alive' not in conn['context']:
                self.remove_connection(conn)

    def read(self, conn: Dict[str, Any]) -> bool:
        try:
            conn['data'] += conn['connection'].recv(1024)
            return True
        except Exception as err:
            self.logger.warn(err)
            self.remove_connection(conn['connection'])
            return False
