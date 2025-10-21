import socket
from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_IN_PORT = int(os.getenv('CLIENT_IN_PORT'))


class NetworkReceiver():
    """
    Class to receive data from a UDP socket.
    """
    def __init__(self, host='localhost', port=CLIENT_IN_PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))

    def receive_data(self):
        data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
        return data.decode('utf-8')