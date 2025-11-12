#pragma once

#include "FIXObject.h"

class Handler {
    public:
        FIXObject handle_message(const FIXObject &fix_obj);
};
