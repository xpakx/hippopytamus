from hippopytamus.protocol.interface import Protocol
from typing import Optional, Dict


class SSHProtocol(Protocol):
    def prepare_response(self, response) -> bytes:
        return response

    def parse_request(self, request: bytes, context: Dict) -> Optional[Dict]:
        if 'payload' in context:
            print(context['payload'])
        if 'read' in context:
            context.pop('read')
        return request

    def feed_parse(self, buffer: bytes, context: Dict) -> (bytes, bool):
        if context == {}:
            context['keep-alive'] = True  # create init method?
        if 'version' not in context:
            if b"\r\n" in buffer:
                context['version'] = buffer
                return buffer, True
            else:
                return buffer, False
        if 'read' not in context:
            context['keep-alive'] = True
            context['read'] = 0
            context['length'] = 0
            context['plength'] = 0
            context['payload'] = b''

        if buffer == b'':
            context.pop('keep-alive')
            return buffer, True

        if context['read'] < 4:
            to_read = 4-context['read']
            n = buffer[:to_read]
            for a in n:
                lu = context['length'] << 8
                lu += a
                context['length'] = lu
            context['read'] += len(n)
            buffer = buffer[to_read:]
        else:
            print(context['length'])

        if context['read'] == 4:
            context['plength'] += buffer[0]
            buffer = buffer[1:]
            context['read'] += 1
        else:
            print(context['plength'])

        payload_length = context['length'] - context['plength'] - 1
        print(payload_length)
        if context['read'] > 4 and len(context['payload']) < payload_length:
            to_read = payload_length-context['read']+5
            n = buffer[:to_read]
            context['payload'] += n
            context['read'] += len(n)
            buffer = buffer[to_read:]
        else:
            print(context['payload'])

        print("READ", context['read'])
        print(buffer)
        if context['read'] > 4 and len(context['payload']) == payload_length:
            print(payload_length)
            return buffer, True

        return buffer, False
