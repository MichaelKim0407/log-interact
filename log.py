import os
import re

from mklibpy.common.collection import SequenceDict
from mklibpy.util.collection import format_list, format_dict

import util

__author__ = 'Michael'


class HandlerMethodNotFound(util.Error):
    pass


class Handler(object):
    @classmethod
    def get_handler_method(cls, cmd):
        cmd_safe = cmd.replace("-", "_")
        if not hasattr(cls, cmd_safe):
            raise HandlerMethodNotFound(
                "`{}` cannot execute command '{}'".format(cls.__name__, cmd))
        return getattr(cls, cmd_safe)

    def execute_cmd(self, cmd, **kwargs):
        return self.get_handler_method(cmd)(self, **kwargs)

    def __repr__(self):
        return self.__class__.__name__


class OpenedFile(Handler):
    def __init__(self, name):
        if not name or not isinstance(name, str):
            raise ValueError
        self.__name = name
        self.__file = open(name)
        self.__size = os.path.getsize(name)

    def __repr__(self):
        return "OpenedFile '{}' {} bytes".format(self.__name, self.__size)

    def close(self, console, **kwargs):
        self.__file.close()
        console.message("File closed")

    def readlines(self, console, **kwargs):
        lines = List(Line)(self.__file.readlines())
        console.message("{} lines read".format(lines.count))
        self.close(console=console, **kwargs)
        return lines


class List(Handler):
    def __init__(self, type):
        self._type = type
        self.__items = []
        self.count = 0

    def __call__(self, items):
        self.__items = list(self._type.items(items))
        self.count = len(self.__items)
        return self

    def __repr__(self):
        return "List<{}>[{}]".format(self._type.__name__, self.count)

    def execute_cmd(self, cmd, **kwargs):
        if cmd in self._type.PROJECTED_TYPE:
            projected_type = self._type.PROJECTED_TYPE[cmd]
            return List(projected_type)(
                [
                    item.execute_cmd(cmd=cmd, **kwargs)
                    for item in self.__items
                    ])
        else:
            return Handler.execute_cmd(self, cmd=cmd, **kwargs)

    def __save_lines(self):
        for item in self.__items:
            yield str(item)

    def print(self, console, **kwargs):
        for line in self.__save_lines():
            console.message(line)
        return self

    def save(self, arg, error, **kwargs):
        try:
            with open(arg, "w") as f:
                for line in self.__save_lines():
                    f.write(line)
                    f.write("\n")
        except IsADirectoryError:
            error("'{}' is a directory")
        return self

    def keep(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")
        return List(self._type)([item for item in self.__items if item.match(arg)])

    def throw(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")
        return List(self._type)([item for item in self.__items if not item.match(arg)])


class Iterable(Handler):
    PROJECTED_TYPE = {}

    def __init__(self, item):
        self._item = item

    def __str__(self):
        return self._item

    @classmethod
    def project(cls, name, type):
        def __decor(func):
            cls.PROJECTED_TYPE[name] = type
            setattr(cls, name.replace("-", "_"), func)
            return func

        return __decor

    @classmethod
    def items(cls, items):
        for item in items:
            if isinstance(item, Iterable):
                yield item
            else:
                yield cls(item)

    def match(self, arg):
        return True


class Line(Iterable):
    def __init__(self, item):
        self._item = item.strip()

    def match(self, arg):
        return re.search(arg, self._item) is not None


class SplitLine(Iterable):
    def __str__(self):
        return format_list(
            self._item,
            start="",
            end="",
            sep="^",
            r=False
        )


class Dictionary(Iterable):
    def __str__(self):
        return format_dict(
            self._item,
            start="",
            end="",
            k_v="=",
            sep="^",
            sort=False,
            r_key=False,
            r_val=False
        )

    def match(self, arg):
        for k in self._item:
            locals()[k] = self._item[k]
        return eval(arg)


@Line.project("split", SplitLine)
def __line_split(self, arg, **kwargs):
    return self._item.split(arg)


@SplitLine.project("take", SplitLine)
def __splitline_take(self, arg, error, **kwargs):
    try:
        return [self._item[int(i)] for i in arg.split()]
    except IndexError or ValueError:
        error("Invalid argument")


@SplitLine.project("int", SplitLine)
def __splitline_int(self, arg, error, **kwargs):
    try:
        indexes = [int(i) for i in arg.split()]
        return [int(self._item[i]) if i in indexes else self._item[i]
                for i in range(len(self._item))]
    except IndexError or ValueError:
        error("Invalid argument")


@SplitLine.project("make-dict", Dictionary)
def __splitline_kv(self, arg, **kwargs):
    d = SequenceDict()
    for i in self._item:
        try:
            k, v = i.split(arg, 1)
        except ValueError:
            k, v = i, None
        d[k] = v
    return d


@Dictionary.project("take", Dictionary)
def __dictionary_take(self, arg, error, **kwargs):
    try:
        d = SequenceDict()
        for k in arg.split():
            d[k] = self._item[k]
        return d
    except KeyError:
        error("Invalid argument")


@Dictionary.project("int", Dictionary)
def __dictionary_int(self, arg, error, **kwargs):
    try:
        d = SequenceDict()
        int_keys = arg.split()
        for k in self._item:
            d[k] = self._item[k]
            if k in int_keys:
                d[k] = int(d[k])
        return d
    except KeyError or ValueError:
        error("Invalid argument")
