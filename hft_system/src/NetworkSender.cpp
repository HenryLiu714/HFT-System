#include "NetworkSender.h"
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>
#include <stdexcept>

NetworkSender::NetworkSender(const std::string &host, int port) {
    // Create UDP socket
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("socket creation failed");
        throw std::runtime_error("Failed to create socket");
    }

    memset(&servaddr, 0, sizeof(servaddr));

    servaddr.sin_family = AF_INET;
    servaddr.sin_port = htons(port);

    // Convert hostname/IP string to binary form
    if (inet_pton(AF_INET, host.c_str(), &servaddr.sin_addr) <= 0) {
        perror("invalid address");
        close(sockfd);
        throw std::runtime_error("Invalid address/host");
    }

    std::cout << "NetworkSender initialized to send to " << host << ":" << port << "\n";
}

NetworkSender::~NetworkSender() {
    close(sockfd);
}

void NetworkSender::send_data(const std::string &data) {
    int sent = sendto(sockfd, data.c_str(), data.size(), 0,
                      (const struct sockaddr *)&servaddr, sizeof(servaddr));
    if (sent < 0) {
        perror("sendto failed");
        throw std::runtime_error("Failed to send data");
    }
}
