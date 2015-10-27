import Queue
import threading
import subprocess
import vim
import shlex
import os
import time

def chomp(string):
    sep_pos = -len(os.linesep)
    if string[sep_pos:] == os.linesep:
            string = string[:sep_pos]
    return string

class CommandResult:
    def __init__(self, pid, command, status, stdout, stderr, time_ms):
        self.pid = str(pid)
        self.command = command
        self.status = str(status)
        self.stdout = stdout
        self.stderr = stderr
        self.time_ms = time_ms

    def name(self):
        return "DoOutput(%s)" % self.pid

class AsyncExecute(threading.Thread):
    def __init__(self, command, output_q, message_q):
        self.__command = command
        self.__output_q = output_q
        self.__message_q = message_q
        threading.Thread.__init__(self)

    def run(self):
        t1 = time.time()
        process = subprocess.Popen(self.__command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        t2 = time.time()
        self.__output_q.put_nowait(CommandResult(process.pid, self.__command,
            process.returncode, out, err, round((t2 - t1) * 1000)))


class CommandResultRenderer:
    def __init__(self, result):
        self.__result = result

    def render(self):
        open_cmd = "new"
        vim.command('silent %s %s' %(open_cmd, self.__result.name()))
        vim.command("setlocal syntax=do_output buftype=nofile modifiable "+ \
                "winfixheight winfixwidth ")
        buffer = vim.current.buffer
        buffer[:] = self.esc(self.header())
        if self.__result.stdout:
            buffer.append(self.esc(self.__result.stdout))
        if self.__result.stderr:
            buffer.append(self.wrap(self.esc(self.__result.stderr), "`"))

    def esc(self, string):
        return chomp(str(string)).split('\n')

    def wrap(self, string, wrap_with):
        return map(lambda x: "%s%s%s" %(wrap_with, x, wrap_with), string)

    def header(self):
        values = (self.__result.command,
                self.__result.status,
                self.__formatted_time(),
                self.__result.pid)
        max_length = max(map(len, values)) + 12

        title = "=" * max_length + "\n"
        title += " [command] %s\n" % values[0]
        title += "  [status] %s\n" % values[1]
        title += "    [time] %s\n" % values[2]
        title += "     [pid] %s\n" % values[3]
        title += "=" * max_length
        return title

    def __formatted_time(self):
        if self.__result.time_ms > 1000.0:
            time = round(self.__result.time_ms / 1000.0, 2)
            unit = "s"
        else:
            time = self.__result.time_ms
            unit = "ms"
        return "{:,}".format(time) + unit

class CommandPool:
    def __init__(self):
        self.__threads = []
        self.__output_q = Queue.Queue(0)
        self.__message_q = Queue.Queue(0)
        self.__au_assigned = False

    def execute(self, command):
        thread = AsyncExecute(command, self.__output_q,
                self.__message_q)
        thread.start()
        self.__threads.append(thread)
        time.sleep(1)
        self.check()
        self._assign_autocommands()
        title = "-" * len(command)

    def check(self):
        try:
            for message in iter(self.__message_q.get_nowait, None):
                print message
        except Queue.Empty:
            pass

        if self.__output_q.empty():
            return

        try:
            for output in iter(self.__output_q.get_nowait, None):
                CommandResultRenderer(output).render()
        except Queue.Empty:
            pass

        self.__threads = [t for t in self.__threads if t.is_alive()]
        if len(self.__threads) == 0:
            self._unassign_autocommands()

    def _assign_autocommands(self):
        if self.__au_assigned:
            return
        vim.command('au CursorHold * python do_async.check()')
        vim.command('au CursorHoldI * python do_async.check()')
        vim.command('au CursorMoved * python do_async.check()')
        vim.command('au CursorMovedI * python do_async.check()')
        vim.command('au FocusGained * python do_async.check()')
        vim.command('au FocusLost * python do_async.check()')
        self.__au_assigned = True

    def _unassign_autocommands(self):
        vim.command('au! CursorHold *')
        vim.command('au! CursorHoldI *')
        vim.command('au! CursorMoved *')
        vim.command('au! CursorMovedI *')
        vim.command('au! FocusGained *')
        vim.command('au! FocusLost *')
        self.__au_assigned = False

