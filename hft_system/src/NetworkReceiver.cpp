#include "NetworkReceiver.h"

#include <arpa/inet.h>
#include <unistd.h>
#include <iostream>
#include <cstring>
#include <stdexcept>

#define BUFFER_SIZE 1024

NetworkReceiver::NetworkReceiver(int port) {
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);

    if (sockfd < 0) {
        perror("socket creation failed");
        throw std::runtime_error("Failed to create socket");
    }

    memset(&servaddr, 0, sizeof(servaddr));
    memset(&cliaddr, 0, sizeof(cliaddr));

    servaddr.sin_family = AF_INET;
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(port);

    // Bind the socket
    if (bind(sockfd, (const struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind failed");
        close(sockfd);
        throw std::runtime_error("Failed to bind socket");
    }

    std::cout << "Receiver listening on port " << port << "...\n";
}

NetworkReceiver::~NetworkReceiver() {
    close(sockfd);
}

std::string NetworkReceiver::receive_data() {
    char buffer[BUFFER_SIZE];
    socklen_t len = sizeof(cliaddr);

    int n = recvfrom(sockfd, buffer, BUFFER_SIZE - 1, 0,
                     (struct sockaddr *)&cliaddr, &len);
    if (n < 0) {
        perror("recvfrom failed");
        throw std::runtime_error("Error receiving data");
    }

    buffer[n] = '\0';  // Null-terminate
    return std::string(buffer);
}


