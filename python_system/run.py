"""
Actual execution module for the python-system package.
"""

import NetworkReceiver, NetworkSender, OrderHandler, Parser, Orderbook

from config import logger

class System():
    def __init__(self):
        self.orderbook = Orderbook.OrderBook()

        self.receiver = NetworkReceiver.NetworkReceiver()
        self.sender = NetworkSender.NetworkSender()
        self.orderhandler = OrderHandler.OrderHandler(self.orderbook)
        self.parser = Parser.Parser()

    def poll(self):
        logger.info("System polling started.")
        while True:
            message = self.receiver.receive_data()
            if not message:
                continue

            fix_message = self.parser.decode_fix(message)
            logger.info("Received FIX message: %s", fix_message)

            return_message = self.orderhandler.handle_order(fix_message)

            if return_message:
                decoded_msg = return_message.decode('utf-8', errors='ignore')
                print(f"SENDING FIX TO EXCHANGE: {decoded_msg}")
                logger.info("Sending response FIX message: %s", decoded_msg)
                self.sender.send_data(decoded_msg)


if __name__ == "__main__":
    system = System()
    system.poll()