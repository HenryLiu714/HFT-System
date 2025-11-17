#include "Parser.h"

#include <sstream>
#include <stdexcept>

FIXObject Parser::parse(const std::string &data) {
    /**
     * @brief Parses the input data.
     * Parses a FIX message string into a FIXObject.
     * Format: tag=value\x01tag=value\x01...
     *
     * @param data The input data to parse in FIX format.
     * @return The parsed FIXObject with all fields populated.
     */

    FIXObject fix_obj;
    
    if (data.empty()) {
        return fix_obj;
    }

    // \x01 is the delimiter
    const char SOH = '\x01';
    
    std::string segmented_string;
    std::istringstream stream(data);
    
    while (std::getline(stream, segmented_string, SOH)) {

        if (segmented_string.empty()) {
            continue;
        }
        
        size_t eq_pos = segmented_string.find('=');
        if (eq_pos == std::string::npos) {
            continue;
        }
        
        // Extracting the tag string and the value.
        std::string tag_string = segmented_string.substr(0, eq_pos);
        std::string value = segmented_string.substr(eq_pos + 1);
        
        // Convert tag string to integer
        try {
            int tag = std::stoi(tag_string);
            fix_obj.set_field(tag, value);
        } catch (const std::invalid_argument& e) {
            // if the tag is not a number
            continue;
        } catch (const std::out_of_range& e) {
            // if the tag value is out of range
            continue;
        }
    }
    
    return fix_obj;
}