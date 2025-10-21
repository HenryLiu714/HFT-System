"""
Contains logic for handling an order from a parsed fix message
"""
import simplefix
import Orderbook

class OrderHandler():
    def __init__(self, orderbook=None):
        self.orderbook = orderbook if orderbook else Orderbook.OrderBook()

    def handle_order(self, fix_message: simplefix.FixMessage):
        # Placeholder for order handling logic

        #TODO: Implement order handling logic here
        return fix_message