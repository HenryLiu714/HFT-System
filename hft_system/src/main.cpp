#include "NetworkReceiver.h"
#include "NetworkSender.h"

#include <iostream>
#include <string>

int main() {
    NetworkReceiver receiver = NetworkReceiver(CLIENT_IN_PORT);
    NetworkSender sender = NetworkSender(RESPONSE_HOST, CLIENT_OUT_PORT);

    std::string data = receiver.receive_data();

    sender.send_data(data);

    std::cout << data << std::endl;
}