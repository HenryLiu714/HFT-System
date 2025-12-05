#include "Parser.h"
#include <stdexcept>

FIXObject Parser::parse(const std::string &data)
{
    /**
     * @brief Parses the input data.
     * Parses a FIX message string into a FIXObject.
     * Format: tag=value\x01tag=value\x01...
     *
     * @param data The input data to parse in FIX format.
     * @return The parsed FIXObject with all fields populated.
     */

    FIXObject fix_obj;

    if (data.empty())
    {
        return fix_obj;
    }

    const char *cursor = data.data();
    const char *end = cursor + data.size();

    while (cursor < end)
    {
        int tag = 0;
        while (cursor < end && *cursor != '=')
        {
            if (*cursor >= '0' && *cursor <= '9')
            {
                tag = tag * 10 + (*cursor - '0');
            }
            cursor++;
        }

        if (cursor == end || *cursor != '=')
        {
            break;
        }

        cursor++;

        const char *value_start = cursor;
        while (cursor < end && *cursor != '\x01')
        {
            cursor++;
        }

        fix_obj.set_field(tag, std::string(value_start, cursor - value_start));

        if (cursor == end)
        {
            break;
        }
        cursor++;
    }

    return fix_obj;
}