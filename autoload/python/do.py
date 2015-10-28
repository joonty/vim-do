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


class CommandResultRenderer:
    def __init__(self, result):
        self.__result = result
        self.__open_cmd = vim.eval('do#get("do_new_buffer_prefix")')
        self.__open_cmd += " %snew" % vim.eval('do#get("do_new_buffer_size")')

    def render(self):
        vim.command('silent %s %s' %(self.__open_cmd, self.__result.name()))
        vim.command("setlocal syntax=do_output buftype=nofile modifiable "+ \
                "winfixheight winfixwidth ")
        buffer = vim.current.buffer
        buffer[:] = self.esc(self.header())
        if self.__result.stdout:
            buffer.append(self.esc(self.__result.stdout))
        if self.__result.stderr:
            buffer.append(self.prepend(self.esc(self.__result.stderr), "E> "))

    def esc(self, string):
        return chomp(str(string)).split('\n')

    def prepend(self, string, prepend_with):
        return map(lambda x: "%s%s" %(prepend_with, x), string)

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

class AsyncExecute(threading.Thread):
    def __init__(self, command, output_q):
        self.__command = command
        self.__output_q = output_q
        threading.Thread.__init__(self)

    def run(self):
        t1 = time.time()
        process = subprocess.Popen(self.__command, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        t2 = time.time()
        self.__output_q.put_nowait(CommandResult(process.pid, self.__command,
            process.returncode, out, err, round((t2 - t1) * 1000)))

class CommandPool:
    def __init__(self):
        self.__threads = []
        self.__output_q = Queue.Queue(0)

    def execute(self, command):
        thread = AsyncExecute(command, self.__output_q)
        thread.start()
        self.__threads.append(thread)

    def any_running(self):
        return len(self.__threads) == 0

    def get_results(self):
        results = []

        if self.__output_q.empty():
            return results

        try:
            for result in iter(self.__output_q.get_nowait, None):
                results.append(result)
        except Queue.Empty:
            pass

        return results

    def cleanup(self):
        self.__threads = [t for t in self.__threads if t.is_alive()]

class Do:
    def __init__(self):
        self.__command_pool = CommandPool()
        self.__au_assigned = False
        self.__results = []

    def execute(self, command):
        self.__command_pool.execute(command)
        self.__assign_autocommands()
        self.check()

    def check(self):
        results = self.__command_pool.get_results()
        if results:
            for result in results:
                CommandResultRenderer(result).render()


        if self.__command_pool.any_running():
            self.__unassign_autocommands()

    def __assign_autocommands(self):
        if self.__au_assigned:
            return
        vim.command('call do#AssignAutocommands()')
        self.__au_assigned = True

    def __unassign_autocommands(self):
        vim.command('call do#UnassignAutocommands()')
        self.__au_assigned = False

