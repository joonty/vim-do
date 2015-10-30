import vim
import window
import logger

class ProcessRenderer:
    def __init__(self):
        self.__command_window = window.CommandWindow()
        self.__command_window.write(CommandWindowHeaderFormat())
        self.__command_window_line_maps = {}

        self.__process_window = window.ProcessWindow()
        self.__process_window_output_line = 0
        self.__process_window_process = None

    def add_process(self, process):
        self.show_process(process)

        (first_line, _) = self.__command_window.write(CommandWindowProcessFormat(process))
        self.__command_window_line_maps[process.get_pid()] = first_line + 1

    def show_process(self, process):
        logger.log("showing process output: %s" % process.get_pid())
        self.__process_window_process = process

        self.__process_window.clean()
        self.__process_window_output_line = 0
        self.__process_window.create(self.__process_window_open_cmd())

        self.__process_window.write(ProcessWindowHeaderFormat(process))
        self.__write_output(process.output().all())

    def __write_output(self, output):
        (first, last) = self.__process_window.write(output)
        self.__process_window_output_line += last - first

    def update_process(self, process):
        self.__command_window.overwrite(CommandWindowProcessFormat(process),
                self.__command_window_line_maps[process.get_pid()],
                True)

        if self.__process_window_process == process:
            logger.log("updating process output: %s" % process.get_pid())
            self.__write_output(process.output().from_line(self.__process_window_output_line))

            if process.has_finished():
                self.__process_window.overwrite(ProcessWindowHeaderFormat(process), 1,
                        True)


    def toggle_command_window(self):
        self.__command_window.toggle("rightbelow 7new")

    def destroy_command_window(self):
        self.__command_window.destroy()

    def destroy_process_window(self):
        self.__process_window.destroy()

    def __process_window_open_cmd(self):
        cmd = vim.eval('do#get("do_new_buffer_prefix")')
        cmd += " %snew" % vim.eval('do#get("do_new_buffer_size")')
        return cmd


class ProcessWindowHeaderFormat:
    def __init__(self, process):
        self.__process = process
        self.__open_cmd = vim.eval('do#get("do_new_buffer_prefix")')
        self.__open_cmd += " %snew" % vim.eval('do#get("do_new_buffer_size")')

    def __str__(self):
        values = (self.__process.get_command(),
                self.__process.get_status(),
                self.__formatted_time(),
                self.__process.get_pid())
        max_length = max(map(len, values)) + 12

        title = "=" * max_length + "\n"
        title += " [command] %s\n" % values[0]
        title += "  [status] %s\n" % values[1]
        title += "    [time] %s\n" % values[2]
        title += "     [pid] %s\n" % values[3]
        title += "=" * max_length
        return title

    def __formatted_time(self):
        time = self.__process.get_time()
        if time > 1000.0:
            time = round(time / 1000.0, 2)
            unit = "s"
        else:
            unit = "ms"
        return "{:,}".format(time) + unit

class CommandWindowHeaderFormat:
    def __str__(self):
        return '''
=============================================================================
 PID     | COMMAND                                             | STATUS
=============================================================================
'''[1:-1]


class CommandWindowProcessFormat:
    def __init__(self, process):
        self.__process = process

    def __str__(self):
        s = ""
        cmd = self.__process.get_command()
        cmd = cmd if len(cmd) <= 30 else cmd[:27] + "..."
        s += " %-7s | %-51s | %s" %(self.__process.get_pid(), cmd,
            self.__process.get_status())
        return s

