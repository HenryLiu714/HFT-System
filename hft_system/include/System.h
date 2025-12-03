#pragma once
#include "NetworkReceiver.h"
#include "NetworkSender.h"
#include "Parser.h"
#include "Handler.h"
#include "Strategy.h"
#include "OrderBook.h"

class System {
private:
    NetworkReceiver* receiver;
    NetworkSender* sender;
    Handler* handler;
    Strategy strategy;
    OrderBook orderbook;
    bool running;
    double price;

public:
    System();
    ~System();
    void start();
    void stop();
};
