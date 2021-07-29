# UDP broadcast case-sender
from socket import *
import time

# Set target address
dest = ('192.168.0.255', 4269)
s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
data = 'I am the client Xiaobai, my time is ()'.format(time.time())
str = s.sendto(data.encode('utf-8'), dest)  # send broadcast
s.settimeout(30)  # Set the waiting timeout time to 30s
msg, addr = s.recvfrom(1024)  # recvfrom is a blocking method
print(f'Receive reply == server address: {addr}, response content: {msg}')
s.close()
