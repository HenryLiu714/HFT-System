#pragma once

#include "config.h"

#include <string>
#include <netinet/in.h>

class NetworkSender {
public:
    NetworkSender(const std::string &host = RESPONSE_HOST, int port = CLIENT_OUT_PORT);
    ~NetworkSender();

    void send_data(const std::string &data);

private:
    int sockfd;
    struct sockaddr_in servaddr;
};
