#include "Handler.h"

FIXObject Handler::handle_message(const FIXObject &fix_obj) {
    /**
     * @brief Handles a FIX message represented by the FIXObject.
     * TODO: Implement actual message handling logic.
     * @param fix_obj The FIXObject containing the message to handle.
     */

     FIXObject sample = FIXObject();
     sample.set_field(35, "0");  // Heartbeat message type
     return sample;
}
