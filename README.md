## Current Pipeline

#### System
1. System polls for messages to be received in FIX protocol format by a NetworkReceiver.
2. Parser object parses message into key-value store (dictionary), passes to an OrderHandler object
3. OrderHandler object receives dictionary, then performs necessary tasks with information. May involve submitting an order, or reading that an order was executed and updating OrderBook. Returns encoded FIX message to send back to exchange.
4. NetworkSender sends return message (if any) back to exchange

#### Exchange
1. Sends FIX messages as necessary (market updates, order executions, etc)
