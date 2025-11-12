#pragma once

#include "NetworkReceiver.h"
#include "NetworkSender.h"
#include "Parser.h"
#include "Handler.h"

class System {
    /**
     * @brief
     * A class representing the overall HFT system.
     */

     public:
        System();
        ~System();

        void start();
        void stop();

    private:
        bool running = false;

        NetworkReceiver* receiver;
        NetworkSender* sender;
        Handler* handler;
};