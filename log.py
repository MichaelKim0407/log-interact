import os as _os
import re as _re

from mklibpy.common.collection import SequenceDict as _SequenceDict
from mklibpy.util.collection import format_list as _format_list, format_dict as _format_dict

import util as _util

__author__ = 'Michael'


class HandlerMethodNotFound(_util.Error):
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
    BY_LINE_THRESHOLD = 1024 * 1024

    def __init__(self, name):
        if not name or not isinstance(name, str):
            raise ValueError
        self.__name = name
        self.__file = open(name)
        self.__size = _os.path.getsize(name)

    def __repr__(self):
        return "OpenedFile '{}' {} bytes".format(self.__name, self.__size)

    def close(self, **kwargs):
        self.__file.close()

    def read_lines(self, console, **kwargs):
        if self.__size >= OpenedFile.BY_LINE_THRESHOLD:
            console.message("File larger than {} bytes, using by-line mode".format(
                OpenedFile.BY_LINE_THRESHOLD))
            return self.read_by_line(console=console, **kwargs)
        else:
            lines = List(Line)(self.__file.readlines())
            self.close(console=console, **kwargs)
            return lines

    def read_by_line(self, **kwargs):
        def __iter():
            for line in self.__file:
                yield line

        def __exit():
            self.close(**kwargs)

        return Iterator(Line, __exit)(__iter)


class List(Handler):
    def __init__(self, type):
        self.__type = type
        self.__items = []
        self.count = 0

    def __call__(self, items):
        self.__items = list(self.__type.items(items))
        self.count = len(self.__items)
        return self

    def __repr__(self):
        return "List<{}>[{}]".format(self.__type.__name__, self.count)

    def execute_cmd(self, cmd, **kwargs):
        if cmd in self.__type.PROJECTED_TYPE:
            projected_type = self.__type.PROJECTED_TYPE[cmd]
            return List(projected_type)(
                [
                    item.execute_cmd(cmd=cmd, **kwargs)
                    for item in self.__items
                    ])
        else:
            return Handler.execute_cmd(self, cmd=cmd, **kwargs)

    def limit(self, arg, error, **kwargs):
        if not arg:
            error("Invalid argument")
        args = arg.split()
        if len(args) <= 0 or len(args) > 3:
            error("Invalid argument")
        return List(self.__type)([self.__items[i] for i in range(*args)])

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

    def store(self, arg, console, **kwargs):
        console.stored_values[arg] = self
        return self

    def keep(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")
        return List(self.__type)([item for item in self.__items if item.match(arg)])

    def throw(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")
        return List(self.__type)([item for item in self.__items if not item.match(arg)])


class Iterator(Handler):
    def __init__(self, type, exit):
        self.__type = type
        self.exit = exit

    def __iter(self):
        pass

    def __call__(self, items_iter):
        self.__iter = self.__type.items_iter(items_iter)
        return self

    def __repr__(self):
        return "Iter<{}>".format(self.__type.__name__)

    def execute_cmd(self, cmd, **kwargs):
        if cmd in self.__type.PROJECTED_TYPE:
            projected_type = self.__type.PROJECTED_TYPE[cmd]

            def __iter():
                for item in self.__iter():
                    yield item.execute_cmd(cmd=cmd, **kwargs)

            return Iterator(projected_type, self.exit)(__iter)
        else:
            return Handler.execute_cmd(self, cmd=cmd, **kwargs)

    def limit(self, arg, error, **kwargs):
        if not arg:
            error("Invalid argument")
        args = arg.split()
        if len(args) <= 0 or len(args) > 3:
            error("Invalid argument")

        if len(args) == 1:
            start, stop, step = 0, int(args[0]), 1
        elif len(args) == 2:
            start, stop, step = int(args[0]), int(args[1]), 1
        else:
            start, stop, step = int(args[0]), int(args[1]), int(args[2])

        def __iter():
            i = 0
            j = start
            for item in self.__iter():
                if i == j:
                    yield item
                    j += step
                    if j >= stop:
                        return
                i += 1

        return Iterator(self.__type, self.exit)(__iter)

    def do(self, **kwargs):
        result = List(self.__type)([item for item in self.__iter()])
        self.exit()
        return result

    def abort(self, **kwargs):
        self.exit()

    def __save_lines(self):
        for item in self.__iter():
            yield str(item)

    def save(self, arg, error, **kwargs):
        try:
            with open(arg, "w") as f:
                for line in self.__save_lines():
                    f.write(line)
                    f.write("\n")
        except IsADirectoryError:
            error("'{}' is a directory")
        self.exit()

    def keep(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")

        def __iter():
            for item in self.__iter():
                if item.match(arg):
                    yield item

        return Iterator(self.__type, self.exit)(__iter)

    def throw(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")

        def __iter():
            for item in self.__iter():
                if not item.match(arg):
                    yield item

        return Iterator(self.__type, self.exit)(__iter)


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

    @classmethod
    def items_iter(cls, items_iter):
        def __iter():
            for item in items_iter():
                if isinstance(item, Iterable):
                    yield item
                else:
                    yield cls(item)

        return __iter

    def match(self, arg):
        return True


class Line(Iterable):
    def __init__(self, item):
        self._item = item.strip()

    def match(self, arg):
        return _re.search(arg, self._item) is not None


class SplitLine(Iterable):
    def __str__(self):
        return _format_list(
            self._item,
            start="",
            end="",
            sep="^",
            r=False
        )


class Dictionary(Iterable):
    def __str__(self):
        return _format_dict(
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


@SplitLine.project("split", SplitLine)
def __splitline_split(self, arg, **kwargs):
    def __iter():
        for item in self._item:
            for i in item.split(arg):
                yield i

    return list(__iter())


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


@SplitLine.project("number", SplitLine)
def __splitline_float(self, arg, error, **kwargs):
    try:
        indexes = [int(i) for i in arg.split()]
        return [float(self._item[i]) if i in indexes else self._item[i]
                for i in range(len(self._item))]
    except IndexError or ValueError:
        error("Invalid argument")


@SplitLine.project("make-dict", Dictionary)
def __splitline_kv(self, arg, **kwargs):
    d = _SequenceDict()
    for i in self._item:
        try:
            k, v = i.split(arg, 1)
        except ValueError:
            k, v = i, None
        d[k] = v
    return d


@SplitLine.project("add-before", SplitLine)
def __splitline_add_before(self, arg, error, **kwargs):
    try:
        index, content = arg.split(None, 1)
        index = int(index)
        return [content + self._item[i] if i == index else self._item[i]
                for i in range(len(self._item))]
    except IndexError or ValueError or TypeError:
        error("Invalid argument")


@SplitLine.project("add-after", SplitLine)
def __splitline_add_after(self, arg, error, **kwargs):
    try:
        index, content = arg.split(None, 1)
        index = int(index)
        return [self._item[i] + content if i == index else self._item[i]
                for i in range(len(self._item))]
    except IndexError or ValueError or TypeError:
        error("Invalid argument")


@SplitLine.project("replace", SplitLine)
def __splitline_add_after(self, arg, error, **kwargs):
    try:
        index, replace, replace_with = arg.split(None, 2)
        index = int(index)
        return [self._item[i].replace(replace, replace_with) if i == index else self._item[i]
                for i in range(len(self._item))]
    except IndexError or ValueError or TypeError:
        error("Invalid argument")


@Dictionary.project("take", Dictionary)
def __dictionary_take(self, arg, error, **kwargs):
    try:
        d = _SequenceDict()
        for k in arg.split():
            d[k] = self._item[k]
        return d
    except KeyError:
        error("Invalid argument")


@Dictionary.project("int", Dictionary)
def __dictionary_int(self, arg, error, **kwargs):
    try:
        d = _SequenceDict()
        int_keys = arg.split()
        for k in self._item:
            d[k] = self._item[k]
            if k in int_keys:
                d[k] = int(d[k])
        return d
    except KeyError or ValueError:
        error("Invalid argument")


@Dictionary.project("number", Dictionary)
def __dictionary_float(self, arg, error, **kwargs):
    try:
        d = _SequenceDict()
        int_keys = arg.split()
        for k in self._item:
            d[k] = self._item[k]
            if k in int_keys:
                d[k] = float(d[k])
        return d
    except KeyError or ValueError:
        error("Invalid argument")
