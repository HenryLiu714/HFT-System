#include "Strategy.h"
#include <string>

Strategy::Strategy() : mean(0.0), count(0), window(20), alpha(0.1) {}

FIXObject Strategy::generate_signal(const OrderBook& ob) {
    double mid = ob.get_midprice();
    if (count < window) {
        mean = mean + alpha * (mid - mean);
        count++;
        return FIXObject();
    }

    FIXObject order;
    if (mid < mean * 0.995) {
        order.set_field(35, "D");
        order.set_field(55, "TEST");
        order.set_field(54, "1");
        order.set_field(38, "10");
        order.set_field(44, std::to_string(ob.get_ask()));
        return order;
    }

    if (mid > mean * 1.005) {
        order.set_field(35, "D");
        order.set_field(55, "TEST");
        order.set_field(54, "2");
        order.set_field(38, "10");
        order.set_field(44, std::to_string(ob.get_bid()));
        return order;
    }

    return FIXObject();
}


