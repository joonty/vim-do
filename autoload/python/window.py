from buffer import *
from utils import log

class Window():
    name = "WINDOW"
    creation_count = 0

    def __init__(self):
        self._buffer = HiddenBuffer()
        self.is_open = False
        self._buffernr = None

    def toggle(self, open_cmd):
        if self.is_open:
            self.destroy()
        else:
            self.create(open_cmd)

    def mark_as_closed(self):
        self.destroy()

    def getbuffernr(self):
        if self._buffernr is None:
            self._buffernr = int(vim.eval("buffer_number('%s')" % self.name))
        return self._buffernr

    def getwinnr(self):
        return int(vim.eval("bufwinnr('%s')" % self.name))

    def set_height(self, height):
        height = int(height)
        minheight = int(vim.eval("&winminheight"))
        if height < minheight:
            height = minheight
        if height <= 0:
            height = 1
        self.command('set winheight=%i' % height)

    def write(self, msg, overwrite = False):
        return self._buffer.write(msg, overwrite)

    def overwrite(self, msg, lineno, allowEmpty = False):
        return self._buffer.overwrite(msg, lineno, allowEmpty)

    def delete(self, start_line, end_line = None):
        self._buffer.delete(start_line, end_line)

    def line_at(self, line):
        return self._buffer.line(line)

    def create(self, open_cmd):
        """ create window """
        if self.is_open:
            return
        vim.command('silent %s %s' %(open_cmd, self.name))
        vim.command("setlocal buftype=nofile modifiable "+ \
                "winfixheight winfixwidth")
        existing_content = self._buffer.contents()
        self._buffer = VimBuffer(vim.buffers[self.getbuffernr()])
        self._buffer.replace(existing_content)
        self.is_open = True
        self.creation_count += 1

        self.on_create()

    def destroy(self, wipeout = True):
        """ destroy window """
        if not self.is_open:
            return
        self.on_destroy()
        self.is_open = False
        self._buffer = HiddenBuffer(self._buffer.contents())
        self._buffernr = None
        if wipeout and int(vim.eval('buffer_exists("%s")' % self.name)) == 1:
            vim.command('bwipeout %s' % self.name)
            log("Wiped out buffer %s" % self.name)

    def clean(self):
        """ clean all data in buffer """
        self._buffer.clean()

    def command(self, cmd):
        """ go to my window & execute command """
        winnr = self.getwinnr()
        if winnr != int(vim.eval("winnr()")):
            vim.command(str(winnr) + 'wincmd w')
        vim.command(str(cmd))

    def on_create(self):
        pass

    def on_destroy(self):
        pass

class ProcessWindow(Window):
    name = "DoProcess"

    def on_create(self):
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s' % self.name
            cmd += ' call do#MarkProcessWindowAsClosed()'
            vim.command(cmd)

        self.command("setlocal syntax=do_output buftype=nofile modifiable "+ \
                "winfixheight winfixwidth")


class CommandWindow(Window):
    name = "DoCommands"
    def on_create(self):
        if self.creation_count == 1:
            cmd = 'silent! au BufWinLeave %s' % self.name
            cmd += ' call do#MarkCommandWindowAsClosed()'
            vim.command(cmd)

        self.command('setlocal syntax=do_command_window')
        self.command('nnoremap <buffer> <cr> '+\
                ':call do#ShowProcessFromCommandWindow()<CR>')
