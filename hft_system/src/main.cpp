#include "System.h"

#include <iostream>
#include <string>

int main() {
    try {
        System hft_system;
        hft_system.start();
    } catch (const std::exception &e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}