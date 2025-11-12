#include "NetworkSender.h"
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <stdexcept>

NetworkSender::NetworkSender(const std::string& target_ip, int target_port) {
    sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        throw std::runtime_error("Failed to create socket");
    }

    memset(&destaddr, 0, sizeof(destaddr));
    destaddr.sin_family = AF_INET;
    destaddr.sin_port = htons(target_port);

    if (inet_pton(AF_INET, target_ip.c_str(), &destaddr.sin_addr) <= 0) {
        close(sockfd);
        throw std::runtime_error("Invalid target address");
    }
}

NetworkSender::~NetworkSender() {
    close(sockfd);
}

void NetworkSender::send_data(const std::string& msg) {
    sendto(sockfd, msg.c_str(), msg.size(), 0,
           (struct sockaddr*)&destaddr, sizeof(destaddr));
}
