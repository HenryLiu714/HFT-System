#pragma once

#include <string>

/**
 * @brief Minimal PnL tracker for the strategy.
 *
 * Tracks:
 *  - position (signed quantity)
 *  - cash PnL from fills
 * and can mark-to-market using the current midprice.
 */
class PnLTracker {
public:
    PnLTracker() : position_(0.0), cash_(0.0) {}

    // side: "1" = buy, "2" = sell
    void on_fill(const std::string& side, double qty, double price);

    double position() const { return position_; }
    double realized_pnl() const { return cash_; }
    double total_pnl(double midprice) const { return cash_ + position_ * midprice; }

private:
    double position_;
    double cash_;
};


