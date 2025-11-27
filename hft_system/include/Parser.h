#pragma once

#include "FIXObject.h"

#include <string>


class Parser {
    public:
        static FIXObject parse(const std::string &data);
};