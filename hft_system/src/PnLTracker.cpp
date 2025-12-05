#include "PnLTracker.h"

void PnLTracker::on_fill(const std::string& side, double qty, double price) {
    if (qty <= 0.0) {
        return;
    }
    if (side == "1") { // Buy
        position_ += qty;
        cash_ -= qty * price;
    } else if (side == "2") { // Sell
        position_ -= qty;
        cash_ += qty * price;
    }
}


