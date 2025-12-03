#include "System.h"
#include <random>
#include <thread>
#include <chrono>

System::System() {
    receiver = new NetworkReceiver(CLIENT_IN_PORT);
    sender = new NetworkSender(RESPONSE_HOST, CLIENT_OUT_PORT);
    handler = new Handler();
    running = false;
    price = 100.0;
}

System::~System() {
    delete receiver;
    delete sender;
    delete handler;
}

void System::start() {
    running = true;

    std::default_random_engine gen;
    std::uniform_int_distribution<int> d(-1, 1);

    while (running) {

        price += d(gen);
        double bid = price - 1.0;
        double ask = price + 1.0;
        orderbook.update(bid, ask);

        FIXObject strat_order = strategy.generate_signal(orderbook);

        if (strat_order.get_field(35) == "D") {
            sender->send_data(strat_order.to_string());

            FIXObject exec;
            exec.set_field(35, "8");
            exec.set_field(39, "2");
            exec.set_field(150, "2");
            exec.set_field(55, strat_order.get_field(55));
            exec.set_field(38, strat_order.get_field(38));
            handler->handle_message(exec);
        }

        std::string data = receiver->receive_data();

        if (!data.empty()) {
            FIXObject fix_obj = Parser::parse(data);
            FIXObject response = handler->handle_message(fix_obj);

            if (!response.to_string().empty()) {
                sender->send_data(response.to_string());
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
}

void System::stop() {
    running = false;
}
