#pragma once

#include <map>
#include <string>
#include <unordered_map>

enum class Side {
    Buy,
    Sell
};

struct Order {
    int order_id;
    int quantity;
    double price;
    Side side;
};

class OrderBook {
    public:
        OrderBook(const std::string &symbol);
        ~OrderBook();

        void add_order(const Order &order);
        void cancel_order(int order_id);
        double get_best_bid(); // if new orderbook for each order, then no need to access Ticker
        double get_best_ask();


    private:
        std::map<double, int, std::greater<double>> bids;
        std::map<double, int> asks;
        std::unordered_map<int, Order> order_index;
        std::string ticker;
};