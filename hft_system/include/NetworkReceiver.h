#pragma once

#include "config.h"

#include <string>
#include <netinet/in.h>

class NetworkReceiver {

    public:
        NetworkReceiver();

        std::string receive_data();

    private:
        int sockfd;
        struct sockaddr_in servaddr, cliaddr;
};