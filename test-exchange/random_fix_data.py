import random
import string
import datetime

# FIX field separator
SOH = "\x01"

# configuration
SYMBOLS = ["AAPL", "GOOG", "MSFT", "TSLA", "AMZN"]
CLIENT_IDS = ["CLIENT_A", "CLIENT_B", "CLIENT_C"]
EXCHANGE_ID = "EXCHANGE_01"
msg_seq_num = 1

# Pricing configuration - NOW VARYING BY SYMBOL
SYMBOL_PRICING = {
    "AAPL": {"base": 175.50, "vol": 2.50},
    "GOOG": {"base": 135.00, "vol": 3.50},
    "MSFT": {"base": 410.25, "vol": 4.00},
    "TSLA": {"base": 240.00, "vol": 5.00},
    "AMZN": {"base": 180.75, "vol": 2.00},
}
DEFAULT_BASE_PRICE = 172.0
DEFAULT_VOLATILITY = 3.0

# ---------------------
# Helper functions

def rand_id(n=8):
    """Generate random uppercase alphanumeric ID."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=n))

def rand_price(symbol=None):
    """
    Return realistic random price (rounded to 2 decimal places),
    now dynamically based on the provided symbol. (FIXED)
    """
    
    # Look up pricing configuration for the symbol, falling back to defaults
    pricing = SYMBOL_PRICING.get(symbol, {})
    base = pricing.get("base", DEFAULT_BASE_PRICE)
    vol = pricing.get("vol", DEFAULT_VOLATILITY)
    
    return round(base + random.uniform(-vol, vol), 2)

def now_ts():
    """Return FIX timestamp: YYYYMMDD-HH:MM:SS.sss (Tag 52: SendingTime)"""
    return datetime.datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")[:-3]

def get_random_sender():
    """Returns a random client ID."""
    return random.choice(CLIENT_IDS)

def get_random_symbol():
    """Returns a random trade symbol."""
    return random.choice(SYMBOLS)


# ---------------------
# Fix (8, 9, 10)

def compute_checksum(s: str) -> str:
    """
    FIX checksum (Tag 10) is the sum of all bytes modulo 256,
    formatted as exactly 3 digits with leading zeros.
    """
    value = sum(ord(c) for c in s) % 256
    return f"{value:03}"


def wrap_fix(fields: dict) -> str:
    """
    Construct a FIX message from a dictionary of tags, ensuring proper tag ordering
    and handling of repeating group tags (stored as tuples).
    """

    header_order = {
        35: 0, # MsgType
        34: 1, # MsgSeqNum
        49: 2, # SenderCompID
        56: 3, # TargetCompID
        52: 4, # SendingTime
    }
    
    body_fields_list = list(fields.items())
    
    def sort_key(item): # This is needed to handle repeating groups correctly (like 269, 270, 271)
        tag = item[0]
        # Repeating group item: (tag_number, index)
        if isinstance(tag, tuple):
            tag_num = tag[0]
            index = tag[1] # Extract the entry index
            return (1, index, tag_num)
        
        # Standard header tag
        if tag in header_order:
            return (0, header_order[tag])
        return (1, tag, 0)

    # Sort the fields according to FIX standards
    body_fields_list.sort(key=sort_key)
    
    body_content = SOH.join(
        f"{item[0] if isinstance(item[0], int) else item[0][0]}={item[1]}" 
        for item in body_fields_list
    ) + SOH

    body_length = len(body_content)
    header = f"8=FIX.4.4{SOH}9={body_length}{SOH}"
    msg_without_checksum = header + body_content
    checksum = compute_checksum(msg_without_checksum)
    
    return msg_without_checksum + f"10={checksum}{SOH}"

# ---------------------
# Message Generators

def gen_logon():
    """Generate a valid Logon message (MsgType=A)."""
    global msg_seq_num
    sender = get_random_sender()
    fields = {
        35: "A",
        34: msg_seq_num,      # MsgSeqNum 
        49: sender,           # SenderCompID (Client)
        56: EXCHANGE_ID,      # TargetCompID (Exchange)
        52: now_ts(),
        98: 0,                # EncryptMethod (None)
        108: 30,              # HeartBtInt (30 seconds)
    }
    
    result = wrap_fix(fields)
    msg_seq_num += 1
    return result


def gen_snapshot(symbol=None):
    """Generate a Market Data Snapshot Full Refresh (MsgType=W)."""
    global msg_seq_num
    symbol = symbol or get_random_symbol()
    levels = random.randint(1, 5) # Random number of MD levels

    fields = {
        35: "W",
        34: msg_seq_num,      # MsgSeqNum
        49: EXCHANGE_ID,      # SenderCompID (Exchange)
        56: get_random_sender(), # TargetCompID (Client)
        55: symbol,           # Symbol
        52: now_ts(),
        268: levels,          # NoMDEntries
    }

    # Repeating group entries (flattened and appended to the dict)
    for i in range(levels):
        # MDEntryType (0=Bid, 1=Offer)
        fields[(269, i)] = random.choice([0, 1])      
        # MDEntryPx (now symbol-specific)
        fields[(270, i)] = rand_price(symbol)         
        # MDEntrySize
        fields[(271, i)] = random.randint(1, 500)

    result = wrap_fix(fields)
    msg_seq_num += 1
    return result


def gen_incremental(symbol=None):
    """Generate a Market Data Incremental Refresh (MsgType=X)."""
    global msg_seq_num
    symbol = symbol or get_random_symbol()
    
    update_action = random.choice([0, 1, 2]) # MDUpdateAction (0=New, 1=Change, 2=Delete)
    
    fields = {
        35: "X",
        34: msg_seq_num,      # MsgSeqNum
        49: EXCHANGE_ID,      # SenderCompID (Exchange)
        56: get_random_sender(), # TargetCompID (Client)
        55: symbol,           # Symbol (optional but good for context)
        52: now_ts(),
        268: 1,               # NoMDEntries (One entry for simplicity)
        279: update_action,
    }
    if update_action != 2: # If not Delete, need price and size
        fields[(269, 0)] = random.choice([0, 1])   # MDEntryType (0=Bid, 1=Offer)
        fields[(270, 0)] = rand_price(symbol)      
        fields[(271, 0)] = random.randint(1, 500)  # MDEntrySize
    
    result = wrap_fix(fields)
    msg_seq_num += 1
    return result


def gen_new_order(symbol=None):
    """Generate a New Order Single (MsgType=D)."""
    global msg_seq_num
    sender = get_random_sender()
    symbol = symbol or get_random_symbol()

    fields = {
        35: "D",
        34: msg_seq_num,      # MsgSeqNum
        49: sender,           # SenderCompID (Client)
        56: EXCHANGE_ID,      # TargetCompID (Exchange)
        11: rand_id(),        # ClOrdID (Client assigned unique ID)
        55: symbol,
        54: random.choice([1, 2]), # Side (1=Buy, 2=Sell)
        38: random.randint(1, 200), # OrderQty
        40: 2,                # OrdType (2=Limit)
    }
    if fields[40] == 2:
        fields[44] = rand_price(symbol) 
        
    fields[60] = now_ts()  # TransactTime
    fields[52] = now_ts()

    result = wrap_fix(fields)
    msg_seq_num += 1
    return result


def gen_cancel(symbol=None):
    """Generate an Order Cancel Request (MsgType=F)."""
    global msg_seq_num
    sender = get_random_sender()
    symbol = symbol or get_random_symbol()

    fields = {
        35: "F",
        34: msg_seq_num,      # MsgSeqNum
        49: sender,           # SenderCompID (Client)
        56: EXCHANGE_ID,      # TargetCompID (Exchange)
        11: rand_id(),        # ClOrdID (New unique ID for the cancel request)
        41: rand_id(),        # OrigClOrdID (ID of the original order to cancel)
        55: symbol,
        54: random.choice([1, 2]), # Side (1=Buy, 2=Sell)
        60: now_ts(),         # TransactTime
        38: random.randint(1, 200), # OrderQty (Required in place of 152)
        52: now_ts(),
    }
    
    result = wrap_fix(fields)
    msg_seq_num += 1
    return result


def gen_execution_report(symbol=None):
    """Generate an Execution Report (MsgType=8)."""
    global msg_seq_num
    symbol = symbol or get_random_symbol()
    qty = random.randint(1, 200)
    filled = random.randint(1, qty) # Always generate at least a partial fill or a full fill
    last_px = rand_price(symbol) 

    fields = {
        35: "8",
        34: msg_seq_num,      # MsgSeqNum
        49: EXCHANGE_ID,      # SenderCompID (Exchange)
        56: get_random_sender(), # TargetCompID (Client)
        11: rand_id(),        # ClOrdID (Client order ID)
        37: rand_id(),        # OrderID (Exchange assigned ID)
        17: rand_id(6),       # ExecID (Unique execution ID for the fill)
        150: "2" if filled == qty else "1", # ExecType (2=Filled, 1=Partial fill)
        39: "2" if filled == qty else "1", 
        55: symbol,
        54: random.choice([1, 2]), # Side
        38: qty,              # OrderQty (Total quantity ordered)
        
        # Tag 39: OrdStatus
        
        32: filled,           # LastShares (Quantity filled in this report)
        31: last_px,          # LastPx (Price of the fill)
        151: qty - filled,    # LeavesQty (Remaining quantity)
        14: filled,           # CumQty (Total filled quantity so far)
        6: last_px,           # AvgPx (Average price, simplified)
        
        52: now_ts(),
    }
    
    result = wrap_fix(fields)
    msg_seq_num += 1
    return result


# ---------------------
# Message Type Registry

MESSAGE_TYPES = [
    gen_logon,
    gen_snapshot,
    gen_incremental,
    gen_new_order,
    gen_cancel,
    gen_execution_report,
]

def generate_random_message():
    """Pick a random message type and return a valid FIX message string."""
    generator = random.choice(MESSAGE_TYPES)
    return generator()

if __name__ == "__main__":
    # Generate and print 5 random FIX messages for debugging
    for _ in range(5):
        print(generate_random_message())