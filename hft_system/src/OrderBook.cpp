#include "../include/OrderBook.h"

OrderBook::OrderBook(const std::string &symbol){
    ticker = symbol;
}

OrderBook::~OrderBook() = default;
void OrderBook::add_order(const Order &order){
    order_index[order.order_id] =  order;
    if (order.side == Side::Buy){
        bids[order.price] += order.quantity;
    }
    if (order.side == Side::Sell){
        asks[order.price] += order.quantity;
    }
}

void OrderBook::cancel_order(int order_id){
    auto it = order_index.find(order_id);
    if (it == order_index.end()) return;

    Order ord = it->second;
    if (ord.side == Side::Buy){
        bids[ord.price] -= ord.quantity;
    }
    if (ord.side == Side::Sell){
        asks[ord.price] -= ord.quantity;
    }
}

double OrderBook::get_best_bid(){
    if (bids.empty()) return 0.0;
    return bids.begin()->first;
}

double OrderBook::get_best_ask(){
    if (asks.empty()) return 0.0;
    return asks.begin()->first;
}