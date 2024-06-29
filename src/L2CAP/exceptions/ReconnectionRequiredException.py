import time


class ReconnectionRequiredException(Exception):
    def __init__(self, message, current_line=0, current_position=0):
        super().__init__(message)
        time.sleep(2)
        self.current_line = current_line
        self.current_position = current_position