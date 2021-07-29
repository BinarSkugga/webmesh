import signal
import socket
import time

from wsproto import WSConnection, ConnectionType
from wsproto.events import Request, AcceptConnection, RejectConnection, CloseConnection, Ping, TextMessage, BytesMessage

connected = True
ws = WSConnection(ConnectionType.CLIENT)
request = Request(host='ws://127.0.0.1:4269', target='/')
data = ws.send(request)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(1)
sock.connect(('127.0.0.1', 4269))
sock.send(data)


def _close(sig, term):
    global connected
    connected = False
    sock.shutdown(socket.SHUT_RDWR)
    time.sleep(1)
    sock.close()


signal.signal(signal.SIGINT, _close)

while connected:
    try:
        data = sock.recv(1024)
        ws.receive_data(data)
        for event in ws.events():
            if isinstance(event, AcceptConnection):
                print('Connection established')
            elif isinstance(event, RejectConnection):
                print('Connection rejected')
            elif isinstance(event, CloseConnection):
                print('Connection closed: code={} reason={}'.format(
                    event.code, event.reason
                ))
                sock.send(ws.send(event.response()))
            elif isinstance(event, Ping):
                print('Received Ping frame with payload {}'.format(event.payload))
                sock.send(ws.send(event.response()))
            elif isinstance(event, TextMessage):
                print('Received TEXT data: {}'.format(event.data))
                if event.message_finished:
                    print('Message finished.')
            elif isinstance(event, BytesMessage):
                print('Received BINARY data: {}'.format(event.data))
                if event.message_finished:
                    print('BINARY Message finished.')
            else:
                print('Unknown event: {!r}'.format(event))
    except socket.timeout:
        pass
