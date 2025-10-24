import simplefix

from config import logger

class Parser(object):
    def __init__(self):
        self.parser = simplefix.FixParser()

    def decode_fix(self, fix_message):
        self.parser.append_buffer(fix_message)

        fix_msg = self.parser.get_message()

        logger.info("Decoded FIX message: %s", fix_msg)

        return fix_msg