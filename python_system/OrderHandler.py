import simplefix
import Orderbook
from datetime import datetime

class OrderHandler:
    def __init__(self, orderbook=None):
        self.orderbook = orderbook if orderbook else Orderbook.OrderBook()
        self.active_orders = {}
        self.seq_num = 1

    def _utc_timestamp(self):
        return datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

    def _compute_checksum(self, msg_str):
        total = sum(ord(ch) for ch in msg_str) % 256
        return f"{total:03}"

    def _build_header(self, msg_type, sender='EXCHANGE', target='CLIENT1'):
        msg = simplefix.FixMessage()
        msg.append_pair(8, 'FIX.4.2')
        msg.append_pair(35, msg_type)
        msg.append_pair(49, sender)
        msg.append_pair(56, target)
        msg.append_pair(34, str(self.seq_num))
        msg.append_pair(52, self._utc_timestamp())
        return msg

    def _finalize_message(self, msg):
        body = msg.encode().decode('utf-8')
        body_len = len(body.split('9=')[0]) + len(body)
        full = f"8=FIX.4.2\x019={body_len}\x01{body}10="
        checksum = self._compute_checksum(full)
        return (full + checksum + "\x01").encode()

    def handle_order(self, fix_message):
        if not fix_message:
            return None

        msg_type_tag = fix_message.get(b'35')
        if not msg_type_tag:
            return None

        msg_type = msg_type_tag.decode()

        #Client logon
        if msg_type == 'A':
            print("LOGON RECEIVED, sending ACK")
            ack = self._build_header('A')
            ack.append_pair(98, '0')
            ack.append_pair(108, '30')
            self.seq_num += 1
            return self._finalize_message(ack)

        #Market data snapshot / incremental
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

            if spread < 0.05 and best_ask != float('inf'):
                return self._build_new_order('AAPL', '1', best_ask)

            return None

        #Execution report
        if msg_type == '8':
            order_id = fix_message.get(b'11').decode()
            status = fix_message.get(b'39').decode()
            self.active_orders[order_id] = status
            print(f"Execution report: {order_id} status={status}")
            return None

        return None

    def _build_new_order(self, symbol, side, price):
        msg = self._build_header('D', sender='CLIENT1', target='EXCHANGE')
        msg.append_pair(11, f"ORD{self.seq_num}")
        msg.append_pair(55, symbol)
        msg.append_pair(54, side)
        msg.append_pair(38, '100')
        msg.append_pair(44, f"{price:.2f}")
        msg.append_pair(40, '2')
        msg.append_pair(59, '0')
        self.seq_num += 1
        return self._finalize_message(msg)
