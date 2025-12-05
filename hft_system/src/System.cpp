#include "System.h"

System::System() {
    /**
     * @brief Constructs a System object, initializing all components.
     */
    receiver = new NetworkReceiver(CLIENT_IN_PORT);
    sender = new NetworkSender(RESPONSE_HOST, CLIENT_OUT_PORT);
    handler = new Handler();
    running = false;
}

System::~System() {
    /**
     * @brief Destroys the System object, cleaning up resources.
     */
    delete receiver;
    delete sender;
    delete handler;
}

void System::start() {
    /**
     * @brief Starts the HFT system, beginning to receive and process messages.
     */
    running = true;
    while (running) {
        std::string data = receiver->receive_data();

        if (data.empty()) {
            continue;  // Skip empty messages
        }

        FIXObject fix_obj = Parser::parse(data);
        FIXObject response = handler->handle_message(fix_obj);

        if (!response.to_string().empty()) {
            sender->send_data(response.to_string());
        }
    }
}

void System::stop() {
    /**
     * @brief Stops the HFT system.
     */
    running = false;
}