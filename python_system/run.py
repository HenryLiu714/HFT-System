"""
Actual execution module for the python-system package.
"""

import NetworkReceiver, NetworkSender, OrderHandler, Parser, Orderbook

class System():
    def __init__(self):
        self.orderbook = Orderbook.OrderBook()

        self.receiver = NetworkReceiver.NetworkReceiver()
        self.sender = NetworkSender.NetworkSender()
        self.orderhandler = OrderHandler.OrderHandler(self.orderbook)
        self.parser = Parser.Parser()

    def poll(self):
        print("Starting system polling...")
        while True:
            message = self.receiver.receive_data()
            if message:
                fix_message = self.parser.decode_fix(message)

                # Process the FIX message and update order book accordingly
                # This is a placeholder for actual processing logic
                return_message = self.orderhandler.handle_order(fix_message)

                self.sender.send_data(return_message)

if __name__ == "__main__":
    system = System()
    system.poll()