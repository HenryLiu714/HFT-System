import simplefix

class Parser(object):
    def __init__(self):
        self.parser = simplefix.FixParser()

    def decode_fix(self, fix_message):
        self.parser.append_buffer(fix_message)

        fix_msg = self.parser.get_message()

        return fix_msg