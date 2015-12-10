import Queue
import threading
import subprocess
import shlex
import select
from utils import log
import os

class AsyncProcessReader(threading.Thread):
    def __init__(self, process, output_q):
        self.__process = process
        self.__output_q = output_q
        threading.Thread.__init__(self)

    def run(self):
        pid = self.__process.pid

        log("Checking output")
        for (stdout, stderr) in self._readfds():
            self.__output_q.put_nowait((pid, None, stdout, stderr))
        log("Collected all output")

        self.__process.wait()
        log("Finished with %i" % self.__process.returncode)
        self.__output_q.put_nowait((pid, self.__process.returncode, None, None))

    def _readfds(self):
        fds = [self.__process.stdout.fileno(), self.__process.stderr.fileno()]
        streams = [self.__process.stdout, self.__process.stderr]

        while self.__process.poll() is None:
            fdsin, _, _ = select.select(fds, [], [])
            for fd in fdsin:
                output = [None, None]
                ind = fds.index(fd)
                stream = streams[ind]
                s = stream.readline()
                if len(s) > 0:
                    output[ind] = s
                    yield output


class ProcessPool:
    def __init__(self):
        self.__threads = []
        self.__output_q = Queue.Queue(0)

    def execute(self, cmd):
        subproc = subprocess.Popen(cmd, shell=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        thread = AsyncProcessReader(subproc, self.__output_q)
        thread.start()
        self.__threads.append(thread)
        return subproc.pid

    def any_running(self):
        self.cleanup()
        return len(self.__threads) == 0

    def get_outputs(self):
        if self.__output_q.empty():
            return []

        results = []
        try:
            for result in iter(self.__output_q.get_nowait, None):
                results.append(result)
        except Queue.Empty:
            pass

        return results

    def cleanup(self):
        self.__threads = [t for t in self.__threads if t.is_alive()]

    def stop(self):
        if self.any_running():
            for t in self.__threads:
                t.join(1000)

