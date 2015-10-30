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
import logger

class Do:
    def __init__(self):
        self.__process_pool = async.ProcessPool()
        self.__processes = ProcessCollection()
        self.__process_renderer = rendering.ProcessRenderer()
        self.__au_assigned = False

    def execute(self, cmd):
        pid = self.__process_pool.execute(cmd)
        logger.log("Started command with pid %i: %s" %(pid, cmd))
        process = self.__processes.add(cmd, pid)
        self.__process_renderer.add_process(process)

        self.__assign_autocommands()
        self.check()

    def __del__(self):
        self.stop()

    def toggle_command_window(self):
        self.__process_renderer.toggle_command_window()

    def mark_command_window_as_closed(self):
        self.__process_renderer.destroy_command_window()

    def mark_process_window_as_closed(self):
        self.__process_renderer.destroy_process_window()

    def check(self):
        logger.log("Checking background threads output")
        outputs = self.__process_pool.get_outputs()
        changed_processes = set()
        for output in outputs:
            if output[1] is not None:
                logger.log("Process %s has finished with exit status %s"
                        %(output[0], output[1]))
            process = self.__processes.update(*output)
            changed_processes.add(process)

        for process in changed_processes:
            self.__process_renderer.update_process(process)

        self.__process_pool.cleanup()
        if self.__processes.all_finished():
            logger.log("All background threads completed")
            self.__unassign_autocommands()

    def enable_logger(self, path):
        logger.Log.set_logger(logger.FileLogger(logger.Logger.DEBUG, path))

    def stop(self):
        self.__process_pool.stop()

    def __assign_autocommands(self):
        if self.__au_assigned:
            return
        logger.log("Assigning autocommands for background checking")
        vim.command('call do#AssignAutocommands()')
        self.__au_assigned = True

    def __unassign_autocommands(self):
        logger.log("Unassigning autocommands")
        vim.command('call do#UnassignAutocommands()')
        self.__au_assigned = False

class ProcessCollection:
    def __init__(self):
        self.__processes = {}

    def add(self, command, pid):
        process = Process(command, pid)
        self.__processes[pid] = process
        return process

    def update(self, pid, exit_status, stdout, stderr):
        process = self.__processes[pid]
        if process is not None:
            if exit_status:
                process.mark_as_complete(exit_status)
            if stdout or stderr:
                process.output().append(stdout, stderr)
        return process

    def all_finished(self):
        return len(filter(lambda p: p.is_running(), self.__processes.values())) == 0

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

