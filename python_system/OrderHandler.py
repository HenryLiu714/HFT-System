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

        # TODO: Implement order handling logic here
        # Want dummy logic for the following:
        # 1. New market data: decide whether to send order, if so return order message
        # 2. Order execution report: update order book accordingly

        return fix_message