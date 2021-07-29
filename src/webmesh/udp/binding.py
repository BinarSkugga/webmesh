# udp broadcast case-receiving end
from socket import *
import time
import traceback

s = socket(AF_INET, SOCK_DGRAM)
# Set up the socket
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
# Choose a receiving address
s.bind(('0.0.0.0', 4269))
while True:
    try:
        msg, addr = s.recvfrom(1024)
        print(f'Receive message == client address: {addr}, message content: {msg}')
        s.sendto("I am the old white of the server, my time is {}".format(time.time()).encode('utf-8'), addr)
    except:
        print("Receive message exception: {}".format(traceback.format_exc()))

s.close()
