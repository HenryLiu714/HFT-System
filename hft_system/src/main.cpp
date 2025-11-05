#include "NetworkReceiver.h"

#include <iostream>
#include <string>

int main() {
    NetworkReceiver receiver = NetworkReceiver();

    std::string data = receiver.receive_data();

    std::cout << data << std::endl;
}