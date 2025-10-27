import simplefix

from config import logger

class Parser(object):
    def __init__(self):
        self.parser = simplefix.FixParser()

    def decode_fix(self, fix_message):
        self.parser.append_buffer(fix_message)
        fix_msg = self.parser.get_message()

        if fix_msg:
            logger.info("Decoded FIX type: %s", type(fix_msg))
            logger.info("Decoded FIX raw bytes: %r", fix_msg.encode())
            logger.info("Decoded FIX tag 35 (MsgType): %s", fix_msg.get(b'35'))
        else:
            logger.info("Decoded FIX message: None")

        return fix_msg
    
    def get_tag_value(self, fix_message, tag):
        return fix_message.get(tag)
