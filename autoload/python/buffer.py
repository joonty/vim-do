import vim

class VimBuffer:
    def __init__(self, buffer):
        self._buffer = buffer

    def replace(self, content):
        self._buffer[:] = content

    def line(self, number):
        return self._buffer[number]

    def write(self, msg, overwrite):
        last_line = len(self._buffer)

        if isinstance(msg, list):
            to_write = msg
        else:
            to_write = str(msg).split('\n')

        if len(to_write) == 1 and to_write[0] == "":
            return (last_line, last_line)

        if overwrite or self.is_empty():
            self._buffer[:] = to_write
        else:
            self._buffer.append(to_write)

        return (last_line, last_line + len(to_write))

    def overwrite(self, msg, lineno, allowEmpty):
        """ insert into current position in buffer"""
        if not msg and allowEmpty == False:
            return

        if isinstance(msg, list):
            to_write = msg
        else:
            to_write = str(msg).split('\n')

        lstart = lineno - 1
        lend = lstart + len(to_write)
        self._buffer[lstart:lend] = to_write

        return (lstart, lend)

    def delete(self, start_line, end_line = None):
        try:
            if not end_line:
                end_line = start_line + 1
            self._buffer[end_line]
            remaining_buffer = self._buffer[end_line:]
            del self._buffer[start_line:]
            self._buffer.append(remaining_buffer)
        except IndexError:
            del self._buffer[start_line:]

    def contents(self):
        return self._buffer[:]

    def clean(self):
        self._buffer[:] = []

    def is_empty(self):
        if len(self._buffer) == 1 and len(self._buffer[0]) == 0:
            return True
        else:
            return False

class HiddenBuffer:
    def __init__(self, buffer = []):
        self._buffer = buffer[:]

    def line(self, number):
        return self._buffer[number]

    def replace(self, contents):
        self._buffer[:] = contents[:]

    def write(self, msg, overwrite):
        last_line = len(self._buffer)

        if isinstance(msg, list):
            to_write = msg
        else:
            to_write = str(msg).split('\n')

        if len(to_write) == 1 and to_write[0] == "":
            return (last_line, last_line)

        to_write = str(msg).split('\n')

        if overwrite or self.is_empty():
            self._buffer[:] = to_write
        else:
            self._buffer.extend(to_write)

        return (last_line, last_line + len(to_write))

    def overwrite(self, msg, lineno, allowEmpty):
        """ insert into current position in buffer"""
        if not msg and allowEmpty == False:
            return

        if isinstance(msg, list):
            to_write = msg
        else:
            to_write = str(msg).split('\n')
        last_line = len(self._buffer)

        lstart = lineno - 1
        lend = lstart + len(to_write)
        self._buffer[lstart:lend] = to_write

        return (lstart, lend)

    def delete(self, start_line, end_line = None):
        try:
            if not end_line:
                end_line = start_line + 1
            self._buffer[start_line:end_line] = []
        except IndexError:
            del self._buffer[start_line:]

    def clean(self):
        self._buffer[:] = []

    def contents(self):
        return self._buffer[:]

    def is_empty(self):
        return not self._buffer


