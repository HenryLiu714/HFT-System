import socket
from dotenv import load_dotenv
import os

load_dotenv()

EXCHANGE_IN_PORT = int(os.getenv('EXCHANGE_IN_PORT'))
EXCHANGE_OUT_PORT = int(os.getenv('EXCHANGE_OUT_PORT'))

CLIENT_IN_PORT = int(os.getenv('CLIENT_IN_PORT'))

class Server(object):
    def __init__(self, host='localhost', in_port=EXCHANGE_IN_PORT, out_port=CLIENT_IN_PORT):
        self.host = host
        self.in_port = in_port
        self.out_port = out_port

        # Setup UDP socket for receiving data
        self.in_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.in_sock.bind((self.host, self.in_port))


        # Setup UDP socket for sending data
        self.out_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.out_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def receive_data(self):
        data, addr = self.in_sock.recvfrom(1024)  # buffer size is 1024 bytes
        return data.decode('utf-8')

    def send_data(self, data):
        self.out_sock.sendto(data.encode('utf-8'), (self.host, self.out_port))


if __name__ == "__main__":
    s = Server()
    print(f"[Exchange] Listening on {s.in_port}, sending to {s.out_port}")
    while True:
        data = s.receive_data()
        print(f"[Exchange] Received: {data}")
        s.send_data("ACK from exchange")
