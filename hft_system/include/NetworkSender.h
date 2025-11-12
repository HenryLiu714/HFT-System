#pragma once

#include "config.h"
#include <string>
#include <netinet/in.h>

class NetworkSender {
public:
    NetworkSender(const std::string& target_ip, int target_port);
    ~NetworkSender();

    void send_data(const std::string& msg);

private:
    int sockfd;
    struct sockaddr_in destaddr;
};
