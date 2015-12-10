import os
import inspect
import sys
directory = os.path.dirname(inspect.getfile(inspect.currentframe()))
sys.path.append(directory)

import rendering
import async
import window
import vim
import time
import string
import signal
from utils import *

class Do:
    def __init__(self):
        self.__process_pool = async.ProcessPool()
        self.__processes = ProcessCollection()
        self.__process_renderer = rendering.ProcessRenderer()
        self.__au_assigned = False
        self.__last_check = time.time() * 1000

    def __del__(self):
        self.stop()

    def execute(self, cmd, quiet = False):
        pid = self.__process_pool.execute(cmd)
        log("Started command with pid %i: %s" %(pid, cmd))
        process = self.__processes.add(cmd, pid)
        self.__process_renderer.add_process(process, quiet)

        self.__assign_autocommands()
        self.check()

    def reload_options(self):
        Options.reload()

    def toggle_command_window(self):
        self.__process_renderer.toggle_command_window()

    def mark_command_window_as_closed(self):
        self.__process_renderer.destroy_command_window()

    def mark_process_window_as_closed(self):
        try:
            self.__process_renderer.destroy_process_window()
        except Exception, e:
            print "Error: %s" % str(e)

    def show_process_from_command_window(self):
        lineno = vim.current.window.cursor[0]
        pid = self.__process_renderer.get_pid_by_line_number(lineno)
        process = self.__processes.get_by_pid(pid)
        if process is not None:
            self.__process_renderer.show_process(process)

    def check(self):
        if (1000 * time.time()) - self.__last_check > Options.check_interval():
            self.check_now()
            self.__last_check = time.time() * 1000

    def check_now(self):
        log("Checking background threads output")
        outputs = self.__process_pool.get_outputs()
        changed_processes = set()
        for output in outputs:
            if output[1] is not None:
                log("Process %s has finished with exit status %s"
                    %(output[0], output[1]))
            process = self.__processes.update(*output)
            changed_processes.add(process)

        for process in changed_processes:
            self.__process_renderer.update_process(process)

        self.__process_pool.cleanup()
        if self.__processes.all_finished():
            log("All background threads completed")
            self.__unassign_autocommands()
        else:
            s = 'feedkeys("\\%s")' % Options.refresh_key()
            log(s)
            vim.eval(s)

    def enable_logger(self, path):
        Log.set_logger(FileLogger(Logger.DEBUG, path))

    def stop(self):
        self.__processes.kill_all()
        self.__process_pool.stop()

    def __assign_autocommands(self):
        if self.__au_assigned:
            return
        log("Assigning autocommands for background checking")
        vim.command('call do#AssignAutocommands()')
        self.__au_assigned = True

    def __unassign_autocommands(self):
        log("Unassigning autocommands")
        vim.command('call do#UnassignAutocommands()')
        self.__au_assigned = False


class ProcessCollection:
    def __init__(self):
        self.__processes = {}

    def add(self, command, pid):
        process = Process(command, pid)
        self.__processes[pid] = process
        return process

    def get_by_pid(self, pid):
        return next((p for p in self.__processes.values() if p.get_pid() == pid), None)

    def update(self, pid, exit_status, stdout, stderr):
        process = self.__processes[pid]
        if process is not None:
            if exit_status is not None:
                process.mark_as_complete(exit_status)
            if stdout or stderr:
                process.output().append(stdout, stderr)
        return process

    def all_finished(self):
        return len(self.get_running()) == 0

    def get_running(self):
        return filter(lambda p: p.is_running(), self.__processes.values())

    def kill_all(self):
        for process in self.get_running():
            process.kill()

class Process:
    def __init__(self, command, pid):
        self.__command = command
        self.__pid = str(pid)
        self.__start_time = time.time()
        self.__output = Output()
        self.__exit_code = None
        self.__time = None

    def mark_as_complete(self, exit_code):
        self.__exit_code = str(exit_code)
        self.__time = round((time.time() - self.__start_time) * 1000)

    def has_finished(self):
        return self.__exit_code is not None

    def is_running(self):
        return not self.has_finished()

    def get_pid(self):
        return self.__pid

    def get_status(self):
        if self.__exit_code is None:
            return "Running"
        else:
            return "exited <%s>" % self.__exit_code

    def get_command(self):
        return self.__command

    def get_time(self):
        if self.__time:
            return self.__time
        else:
            return round((time.time() - self.__start_time) * 1000)

    def output(self):
        return self.__output

    def name(self):
        return "DoOutput(%s)" % self.__pid

    def kill(self):
        try:
            os.kill(int(self.__pid), signal.SIGTERM)
        except:
            pass


class Output:
    def __init__(self):
        self.__output = []

    def all(self):
        return self.__output

    def __len__(self):
        return len(self.__output)

    def from_line(self, line):
        return self.__output[line:]

    def append(self, stdout, stderr):
        if stdout is not None:
            self.__output.append(stdout)
        if stderr is not None:
            self.__output.append("E> %s" % stderr)
