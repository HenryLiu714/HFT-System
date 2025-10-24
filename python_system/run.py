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
            if message:
                fix_message = self.parser.decode_fix(message)
                logger.info("Received FIX message: %s", fix_message)

                # Process the FIX message and update order book accordingly
                # This is a placeholder for actual processing logic
                return_message = self.orderhandler.handle_order(fix_message)
                logger.info("Sending response FIX message: %s", return_message)

                self.sender.send_data(return_message)

if __name__ == "__main__":
    system = System()
    system.poll()