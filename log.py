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


class Collection(Handler):
    def __init__(self, type):
        self._type = type

    def __repr__(self):
        return "{}<{}>".format(self.__class__.__name__, self._type.__name__)

    def __iter__(self):
        pass

    def get_items(self, type, converter=None, match=None):
        if converter is None:
            converter = lambda x: x
        if match is None:
            match = lambda x: True
        return self._get_items(type, converter, match)

    def _get_items(self, type, converter, match):
        pass

    def execute_cmd(self, cmd, **kwargs):
        if cmd in self._type.PROJECTED_TYPE:
            projected_type = self._type.PROJECTED_TYPE[cmd]
            return self.get_items(projected_type,
                                  converter=lambda item: item.execute_cmd(cmd=cmd, **kwargs))
        else:
            try:
                return Handler.execute_cmd(self, cmd=cmd, **kwargs)
            except HandlerMethodNotFound:
                raise HandlerMethodNotFound(
                    "`{!r}` cannot execute command '{}'".format(self, cmd))

    def keep(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")
        return self.get_items(self._type, match=lambda item: item.match(arg))

    def throw(self, arg, error, **kwargs):
        if arg is None:
            error("Please specify criteria")
        return self.get_items(self._type, match=lambda item: not item.match(arg))

    def _save_lines(self):
        for item in self:
            yield str(item)

    def save(self, arg, error, **kwargs):
        try:
            with open(arg, "w") as f:
                for line in self._save_lines():
                    f.write(line)
                    f.write("\n")
        except IsADirectoryError:
            error("'{}' is a directory")

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
            for item in self:
                if i == j:
                    yield item
                    j += step
                    if j >= stop:
                        return
                i += 1

        return __iter


class List(Collection):
    def __init__(self, type):
        Collection.__init__(self, type)
        self.__items = []

    def __call__(self, items):
        self.__items = list(self._type.items(items))
        return self

    def __repr__(self):
        return Collection.__repr__(self) + "[{}]".format(len(self))

    def __iter__(self):
        return self.__items.__iter__()

    def __len__(self):
        return len(self.__items)

    def _get_items(self, type, converter, match):
        return List(type)([converter(item) for item in self if match(item)])

    def limit(self, **kwargs):
        return List(self._type)([item for item in Collection.limit(self, **kwargs)()])

    def print(self, console, **kwargs):
        for line in self._save_lines():
            console.message(line)
        return self

    def save(self, **kwargs):
        Collection.save(self, **kwargs)
        return self

    def store(self, arg, console, **kwargs):
        console.stored_values[arg] = self
        return self


class Iterator(Collection):
    def __init__(self, type, exit):
        Collection.__init__(self, type)
        self.exit = exit

    def __iter__(self):
        return self.__iter()

    def __iter(self):
        pass

    def __call__(self, items_iter):
        self.__iter = self._type.items_iter(items_iter)
        return self

    def _get_items(self, type, converter, match):
        def __iter():
            for item in self:
                if match(item):
                    yield converter(item)

        return Iterator(type, self.exit)(__iter)

    def limit(self, **kwargs):
        return Iterator(self._type, self.exit)(Collection.limit(self, **kwargs))

    def do(self, **kwargs):
        result = List(self._type)([item for item in self])
        self.exit()
        return result

    def abort(self, **kwargs):
        self.exit()

    def save(self, **kwargs):
        Collection.save(self, **kwargs)
        self.exit()


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
