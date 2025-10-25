import simplefix
import Orderbook

class OrderHandler:
    def __init__(self, orderbook=None):
        self.orderbook = orderbook if orderbook else Orderbook.OrderBook()
        self.active_orders = {}

    def handle_order(self, fix_message):
        if not fix_message:
            return None

        msg_type_raw = fix_message.get(b'35')
        print(f"[DEBUG] RAW FIX TAG 35 VALUE: {msg_type_raw}")

        if not msg_type_raw:
            print("[DEBUG] No MsgType tag found in message")
            return None

        msg_type = msg_type_raw.decode()
        print(f"[DEBUG] DECODED MsgType: {msg_type}")


        msg_type = fix_message.get(b'35').decode()

        if msg_type == 'A':
            print("LOGON RECEIVED → sending ACK")
            ack = simplefix.FixMessage()
            ack.append_pair(8, 'FIX.4.2')      
            ack.append_pair(9, '70')            
            ack.append_pair(35, 'A')           
            ack.append_pair(49, 'EXCHANGE')      
            ack.append_pair(56, 'CLIENT1')      
            ack.append_pair(98, '0')
            ack.append_pair(108, '30')        
            ack.append_pair(10, '000')    
            return ack.encode()


        if msg_type in ('W', 'X'):
            side_tag = fix_message.get(b'269')
            price = float(fix_message.get(b'270'))
            size = int(fix_message.get(b'271'))

            if side_tag == b'0':
                self.orderbook.update('buy', price, size)
            elif side_tag == b'1':
                self.orderbook.update('sell', price, size)

            best_bid = max(self.orderbook.bids.keys(), default=0)
            best_ask = min(self.orderbook.asks.keys(), default=float('inf'))
            spread = best_ask - best_bid

            if spread < 0.05:
                return self._build_order('AAPL', '1', best_ask)

            return None

        if msg_type == '8':
            order_id = fix_message.get(b'11').decode()
            status = fix_message.get(b'39').decode()
            self.active_orders[order_id] = status
            print(f"Execution report: {order_id} status={status}")
            return None

        return None

    def _build_order(self, symbol, side, price):
        msg = simplefix.FixMessage()
        msg.append_pair(35, 'D')
        msg.append_pair(49, 'CLIENT1')
        msg.append_pair(56, 'EXCHANGE')
        msg.append_pair(55, symbol)
        msg.append_pair(54, side)
        msg.append_pair(38, '100')
        msg.append_pair(44, str(price))
        msg.append_pair(40, '2')
        msg.append_pair(59, '0')
        return msg.encode()
