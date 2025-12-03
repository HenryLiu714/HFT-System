#pragma once

#include "OrderBook.h"
#include "FIXObject.h"

class Strategy {
private:
    double mean;
    int count;
    int window;
    double alpha;

public:
    Strategy();
    FIXObject generate_signal(const OrderBook& ob);
};


