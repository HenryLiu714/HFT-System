import socket

from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_OUT_PORT = int(os.getenv('EXCHANGE_IN_PORT'))

class NetworkSender():
    def __init__(self, host='localhost', port=CLIENT_OUT_PORT):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_data(self, data):
        self.sock.sendto(data.encode('utf-8'), (self.host, self.port))

