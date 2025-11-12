#pragma once

#include <unordered_map>
#include <string>

class FIXObject {
    /**
     * @brief
     * A class representing a FIX (Financial Information eXchange) message object.
     */

     public:
        FIXObject() = default;
        ~FIXObject() = default;

        void set_field(int tag, const std::string &value);

        std::string get_field(int tag);

        std::string to_string() const;

    private:
        std::unordered_map<int, std::string> fields;
};