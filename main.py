#!/usr/bin/python3

from mklibpy.terminal import clear_screen as _clear_screen
from mklibpy.terminal.interact import user_input as _user_input

import command as _command
import util as _util

__author__ = 'Michael'


class Console(object):
    def __init__(self):
        _clear_screen()
        self.result = None
        self.stored_values = {}

    def single_line(self, line):
        if not line:
            return
        try:
            cmd, arg = line.split(None, 1)
        except ValueError:
            cmd, arg = line, None
        self.result = _command.execute(
            cmd,
            arg=arg,
            last=self.result,
            console=self,
            error=self.error
        )

    def line(self, line):
        MultiLineGroup(line).execute(self)

    def exit(self):
        raise _util.ExitCommand

    def reset(self):
        raise _util.ResetCommand

    def error(self, message):
        raise _util.Error(message)

    def message(self, message):
        _util.message(message)

    def print(self):
        if self.result is not None:
            _util.result(repr(self.result))


class SingleLine(object):
    def __init__(self, line):
        self.line = line.strip()

    def execute(self, console):
        console.single_line(self.line)


class MultiLine(object):
    def __init__(self, line):
        self.lines = [SingleLine(l) for l in line.split("&&")]

    def execute(self, console):
        try:
            for l in self.lines:
                l.execute(console)
        except _util.Error as e:
            _util.error(e.msg)


class MultiLineGroup(object):
    def __init__(self, line):
        if "#" in line:
            line = line.split("#")[0]
        self.lines = [MultiLine(l) for l in line.split(";")]

    def execute(self, console):
        for l in self.lines:
            l.execute(console)


def main():
    console = Console()
    while True:
        try:
            line = _user_input("> ")
            console.line(line)
        except _util.ResetCommand:
            console = Console()
            continue
        except _util.ExitCommand:
            break
        console.print()


def script(name):
    console = Console()
    console.line("run " + name)


if __name__ == "__main__":
    from sys import argv

    if len(argv) <= 1:
        main()
    else:
        script(argv[1])
