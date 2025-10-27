
class OrderBook(object):
    def __init__(self):
        self.bids = {}
        self.asks = {}

    def update(self, side, price, size):
        if side == 'buy':
            if size == 0:
                if price in self.bids:
                    del self.bids[price]
            else:
                self.bids[price] = size
        elif side == 'sell':
            if size == 0:
                if price in self.asks:
                    del self.asks[price]
            else:
                self.asks[price] = size

    def __repr__(self):
        return f"Bids: {self.bids} | Asks: {self.asks}"
