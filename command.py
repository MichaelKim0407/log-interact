import log as _log
import util as _util

__author__ = 'Michael'

__commands = {}


def command(name):
    def __decor(func):
        __commands[name] = func
        return func

    return __decor


def execute(name, **kwargs):
    if name not in __commands:
        raise _util.Error("Command '{}' not found".format(name))
    return __commands[name](cmd=name, **kwargs)


# -----

@command("exit")
def __cmd_exit(console, **kwargs):
    console.exit()


@command("reset")
def __cmd_reset(console, **kwargs):
    console.reset()


@command("open")
def __cmd_file_open(arg, error, **kwargs):
    if not arg:
        error("Please specify a file")
    try:
        return _log.OpenedFile(arg)
    except ValueError:
        error("Invalid argument")
    except FileNotFoundError:
        error("File '{}' does not exist".format(arg))
    except IsADirectoryError:
        error("'{}' is a directory".format(arg))


@command("run")
def __cmd_run(arg, error, console, **kwargs):
    if not arg:
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


@command("-")
def __cmd_sep(last, console, **kwargs):
    console.message("")
    return last


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
@command("store")
@command("sort")
@command("count")
@command("sum")
def __cmd_common(last, error, **kwargs):
    if last is None:
        error("Nothing to operate")
    return last.execute_cmd(error=error, **kwargs)


@command("load")
def __cmd_load(arg, error, console, **kwargs):
    if arg in console.stored_values:
        return console.stored_values[arg]
    else:
        error("Value '{}' not found".format(arg))
