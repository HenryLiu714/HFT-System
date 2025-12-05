#include "Handler.h"
#include "FIXObject.h"

FIXObject Handler::handle_message(const FIXObject &fix_obj) {
    std::string msg_type = fix_obj.get_field(35); //read message type

    FIXObject resp;

    if (msg_type == "0") { //heartbeat
        resp.set_field(35, "0");
        return resp;
    }

    if (msg_type == "1") { //hearbeat
        resp.set_field(35, "0");
        resp.set_field(112, fix_obj.get_field(112));
        return resp;
    }

    if (msg_type == "A") { //logon
        resp.set_field(35, "A");
        resp.set_field(98, "0");
        resp.set_field(108, "30");
        return resp;
    }

    if (msg_type == "D") { //execution
        resp.set_field(35, "8");
        resp.set_field(150, "0");
        resp.set_field(39, "0");
        resp.set_field(11, fix_obj.get_field(11));
        resp.set_field(55, fix_obj.get_field(55));
        resp.set_field(54, fix_obj.get_field(54));
        resp.set_field(38, fix_obj.get_field(38));
        return resp;
    }

    return resp;
}
