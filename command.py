import log
import util

__author__ = 'Michael'

__commands = {}


def command(name):
    def __decor(func):
        __commands[name] = func
        return func

    return __decor


def execute(name, **kwargs):
    if name not in __commands:
        raise util.Error("Command '{}' not found".format(name))
    return __commands[name](cmd=name, **kwargs)


# -----

@command("exit")
def cmd_exit(console, **kwargs):
    console.exit()


@command("reset")
def cmd_reset(console, **kwargs):
    console.reset()


@command("open")
def cmd_file_open(arg, error, **kwargs):
    if arg is None:
        error("Please specify a file")
    try:
        return log.OpenedFile(arg)
    except ValueError:
        error("Invalid argument")
    except FileNotFoundError:
        error("File '{}' does not exist".format(arg))
    except IsADirectoryError:
        error("'{}' is a directory".format(arg))


@command("run")
def cmd_run(arg, error, console, **kwargs):
    if arg is None:
        error("Please specify a script")
    try:
        with open(arg) as f:
            for line in f:
                console.line(line)
    except FileNotFoundError:
        error("File '{}' does not exist".format(arg))
    except IsADirectoryError:
        error("'{}' is a directory".format(arg))
    else:
        return console.result


@command("close")
@command("read-lines")
@command("read-by-line")
@command("split")
@command("make-dict")
@command("print")
@command("save")
@command("keep")
@command("throw")
@command("take")
@command("int")
@command("number")
@command("do")
@command("abort")
@command("add-before")
@command("add-after")
@command("replace")
@command("limit")
def cmd_common(last, error, **kwargs):
    if last is None:
        error("Nothing to operate")
    return last.execute_cmd(error=error, **kwargs)
