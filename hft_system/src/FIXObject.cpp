#include "FIXObject.h"

void FIXObject::set_field(int tag, const std::string &value) {
    /**
     * @brief Sets the value for a given FIX tag.
     *
     * @param tag The FIX tag number.
     * @param value The value to set for the tag.
     */
    fields[tag] = value;
}

std::string FIXObject::get_field(int tag) const {
    /**
     * @brief Retrieves the value for a given FIX tag.
     *
     * @param tag The FIX tag number.
     * @return The value associated with the tag, or an empty string if not found.
     */
    auto it = fields.find(tag);
    if (it != fields.end()) {
        return it->second;
    }
    return "";
}

std::string FIXObject::to_string() const {
    /**
     * @brief Converts the FIXObject to a string representation.
     *
     * @return A string representation of the FIXObject.
     */
    std::string result;
    for (const auto &pair : fields) {
        result += std::to_string(pair.first) + "=" + pair.second + "\x01";  // SOH delimiter
    }
    return result;
}