#!/usr/bin/python3

import os
import platform
import re

__author__ = 'Michael'

# --- util.py ---

if platform.system() == "Windows":
    def clear_screen():
        os.system("cls")
else:
    def clear_screen():
        os.system("clear")


class ExitCommand(Exception):
    pass


class ResetCommand(Exception):
    pass


class Error(Exception):
    def __init__(self, msg):
        self.msg = msg


class SequenceDict(object):
    """
    A dictionary in which keys are sequenced.
    """

    def __init__(self, keys=None, values=None):
        if keys is None:
            keys = []
        if values is None:
            values = []
        self.__keys = keys
        self.__dict = {}

        for i in range(len(keys)):
            self.__dict[keys[i]] = values[i]

    # --- Container methods ---
    # See: https://docs.python.org/3/reference/datamodel.html#emulating-container-types

    def __len__(self):
        return self.__keys.__len__()

    def __getitem__(self, item):
        return self.__dict.__getitem__(item)

    def __setitem__(self, key, value):
        if key not in self.__keys:
            self.__keys.append(key)
        self.__dict.__setitem__(key, value)

    def __delitem__(self, key):
        self.__keys.remove(key)
        self.__dict.__delitem__(key)

    def __iter__(self):
        return self.__keys.__iter__()

    def __reversed__(self):
        return self.__keys.__reversed__()

    def __contains__(self, item):
        return self.__keys.__contains__(item)

    # --- SequenceDict operations ---

    def clear(self):
        self.__keys.clear()
        self.__dict.clear()

    def copy(self):
        return SequenceDict(*self.__keys, **self.__dict)

    def index(self, value, start=None, stop=None):
        if start is None:
            return self.__keys.index(value)
        elif stop is None:
            return self.__keys.index(value, start)
        else:
            return self.__keys.index(value, start, stop)

    def insert(self, index, key, value):
        self.__keys.insert(index, key)
        self[key] = value

    def keys(self):
        return list(self.__keys)

    def pop(self, key):
        self.__keys.remove(key)
        return self.__dict.pop(key)

    def pop_at(self, index):
        key = self.__keys.pop(index)
        val = self.__dict.pop(key)
        return key, val

    def reverse(self):
        self.__keys.reverse()

    def sort(self, key=None, reverse=False):
        self.__keys.sort(key=key, reverse=reverse)

    def sort_by_value(self, key=None, reverse=False):
        if key is not None:
            key = lambda x: key(self[x])
        self.__keys.sort(key=key, reverse=reverse)

    def values(self):
        def __gen():
            for key in self:
                yield self[key]

        return list(__gen())


class SortedDict(object):
    def __init__(self, order=None):
        """

        :param reversed:
            None (default): not sorted
            "+": ascending
            "-": descending
        """
        self.__keys = []
        self.__dict = {}
        self.__order = order

    def __getitem__(self, key):
        return self.__dict[key]

    def __contains__(self, item):
        return item in self.__keys

    def __iter__(self):
        return self.__keys.__iter__()

    def __len__(self):
        return len(self.__keys)

    def __setitem__(self, key, value):
        if key not in self.__keys:
            if self.__order == "+":
                for i in range(len(self.__keys)):
                    if self.__keys[i] > key:
                        self.__keys.insert(i, key)
                        break
                else:
                    self.__keys.append(key)
            elif self.__order == "-":
                for i in range(len(self.__keys)):
                    if self.__keys[i] < key:
                        self.__keys.insert(i, key)
                        break
                else:
                    self.__keys.append(key)
            else:
                self.__keys.append(key)
        self.__dict[key] = value


def resolve_group_args(*args):
    i = None
    for arg in args:
        if i is None:
            i = arg
            continue
        if arg in ["+", "-"]:
            yield i, arg
            i = None
        else:
            yield i, None
            i = arg
    if i is not None:
        yield i, None


# --- log.py ---

class HandlerMethodNotFound(Error):
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
        self.__size = os.path.getsize(name)

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
        arg = kwargs["arg"]
        if arg and "@" in arg and cmd != "group":
            arg1, arg2 = [a.strip() for a in arg.rsplit("@", 1)]
            console = kwargs["console"]
            if cmd == "sort":
                line = "group @ {} && un-group".format(arg2)
            else:
                line = "group @ {} && {} {} && un-group".format(arg2, cmd, arg1)
            console.line(line)
            return console.result
        elif cmd in self._type.PROJECTED_TYPE:
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
        if not arg:
            error("Please specify criteria")
        return self.get_items(self._type, match=lambda item: item.match(arg))

    def throw(self, arg, error, **kwargs):
        if not arg:
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

    def group(self, arg, error, **kwargs):
        if self._type is not Dictionary:
            error("`group` can only apply to Dictionary")
        if not arg:
            error("Invalid argument")
        args = arg.split()
        if args[0] != "@":
            error("Invalid argument")
        if len(args) < 2:
            error("Invalid argument")
        group = Group(*resolve_group_args(*args[1:]))
        try:
            for item in self:
                group.append(item)
        except KeyError:
            error("Invalid argument")
        return group


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
            console.output(line)
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
        return re.search(arg, self._item) is not None


class SplitLine(Iterable):
    def __str__(self):
        result = ""
        first = True
        for item in self:
            if first:
                first = False
            else:
                result += "^"
            result += str(item)
        return result

    def __iter__(self):
        return self._item.__iter__()

    def __len__(self):
        return self._item.__len__()

    def __getitem__(self, item):
        return self._item.__getitem__(item)


class Dictionary(Iterable):
    def __str__(self):
        result = ""
        first = True
        for key in self:
            if first:
                first = False
            else:
                result += "^"
            result += str(key) + "=" + str(self[key])
        return result

    def __iter__(self):
        return self._item.__iter__()

    def __getitem__(self, item):
        return self._item.__getitem__(item)

    def __contains__(self, item):
        return self._item.__contains__(item)

    def match(self, arg):
        for k in self:
            locals()[k] = self[k]
        return eval(arg)


@Line.project("split", SplitLine)
def __line_split(self, arg, **kwargs):
    return self._item.split(arg)


@SplitLine.project("split", SplitLine)
def __splitline_split(self, arg, **kwargs):
    def __iter():
        for item in self:
            for i in item.split(arg):
                yield i

    return list(__iter())


@SplitLine.project("take", SplitLine)
def __splitline_take(self, arg, error, **kwargs):
    try:
        return [self[int(i)] for i in arg.split()]
    except IndexError or ValueError:
        error("Invalid argument")


@SplitLine.project("int", SplitLine)
def __splitline_int(self, arg, error, **kwargs):
    try:
        indexes = [int(i) for i in arg.split()]
        return [int(self[i]) if i in indexes else self[i]
                for i in range(len(self))]
    except IndexError or ValueError:
        error("Invalid argument")


@SplitLine.project("number", SplitLine)
def __splitline_float(self, arg, error, **kwargs):
    try:
        indexes = [int(i) for i in arg.split()]
        return [float(self[i]) if i in indexes else self[i]
                for i in range(len(self))]
    except IndexError or ValueError:
        error("Invalid argument")


@SplitLine.project("make-dict", Dictionary)
def __splitline_kv(self, arg, **kwargs):
    d = SequenceDict()
    for i in self:
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
        length = len(self)
        return [content + self[i] if i == index % length  else self[i]
                for i in range(length)]
    except IndexError or ValueError or TypeError:
        error("Invalid argument")


@SplitLine.project("add-after", SplitLine)
def __splitline_add_after(self, arg, error, **kwargs):
    try:
        index, content = arg.split(None, 1)
        index = int(index)
        length = len(self)
        return [self[i] + content if i == index % length else self[i]
                for i in range(length)]
    except IndexError or ValueError or TypeError:
        error("Invalid argument")


@SplitLine.project("replace", SplitLine)
def __splitline_add_after(self, arg, error, **kwargs):
    try:
        index, replace, replace_with = arg.split(None, 2)
        index = int(index)
        length = len(self)
        return [self[i].replace(replace, replace_with) if i == index % length else self[i]
                for i in range(length)]
    except IndexError or ValueError or TypeError:
        error("Invalid argument")


@Dictionary.project("take", Dictionary)
def __dictionary_take(self, arg, error, **kwargs):
    try:
        d = SequenceDict()
        for k in arg.split():
            d[k] = self[k]
        return d
    except KeyError:
        error("Invalid argument")


@Dictionary.project("int", Dictionary)
def __dictionary_int(self, arg, error, **kwargs):
    try:
        d = SequenceDict()
        int_keys = arg.split()
        for k in self:
            d[k] = self[k]
            if k in int_keys:
                d[k] = int(d[k])
        return d
    except KeyError or ValueError:
        error("Invalid argument")


@Dictionary.project("number", Dictionary)
def __dictionary_float(self, arg, error, **kwargs):
    try:
        d = SequenceDict()
        int_keys = arg.split()
        for k in self:
            d[k] = self[k]
            if k in int_keys:
                d[k] = float(d[k])
        return d
    except KeyError or ValueError:
        error("Invalid argument")


@Dictionary.project("rename", Dictionary)
def __dictionary_rename(self, arg, error, **kwargs):
    if not arg:
        error("Invalid argument")
    args = arg.split()
    if len(args) != 2:
        error("Invalid argument")
    old_key, new_key = args
    if old_key not in self:
        error("Invalid argument")
    elif new_key in self:
        error("Invalid argument")
    d = SequenceDict()
    for key in self:
        if key == old_key:
            d[new_key] = self[old_key]
        else:
            d[key] = self[key]
    return d


class Group(Handler):
    def __init__(self, *keys):
        self.__keys = list(keys)
        key = self.__keys.pop(0)
        if isinstance(key, list) or isinstance(key, tuple):
            self.__key, self.__sort = key
        else:
            self.__key, self.__sort = key, None

        self.__items = SortedDict(self.__sort)

    def __repr__(self):
        def __formatter(k, s):
            if s is None:
                return k
            else:
                return k + " " + s

        result = "Group ["
        result += __formatter(self.__key, self.__sort)
        for k, s in self.__keys:
            result += ", "
            result += __formatter(k, s)
        result += "]"
        return result

    def __iter(self, *kvs):
        kvs = list(kvs)
        if self.__keys:
            for val in self.__items:
                for i in self[val].__iter(*(kvs + [(self.__key, val)])):
                    yield i
        else:
            for val in self.__items:
                yield (kvs + [(self.__key, val)], self[val])

    def __iter__(self):
        for kvs, l in self.__iter():
            for item in l:
                yield item

    def __getitem__(self, item):
        return self.__items.__getitem__(item)

    def __setitem__(self, key, value):
        return self.__items.__setitem__(key, value)

    def append(self, item):
        val = item[self.__key]
        if val not in self.__items:
            if self.__keys:
                self[val] = Group(*self.__keys)
            else:
                self[val] = []
        self[val].append(item)

    def un_group(self, **kwargs):
        a = List(Dictionary)(self)
        return a

    def __new_group(self, converter=None, l_converter=None):
        group = Group((self.__key, self.__sort), *self.__keys)

        if l_converter is not None:
            for kvs, l in self.__iter():
                group.append(l_converter(kvs, l))
        elif converter is not None:
            for kvs, l in self.__iter():
                for item in l:
                    group.append(converter(kvs, item))
        else:
            raise ValueError

        return group

    def add_count(self, arg, **kwargs):
        if not arg:
            arg = "count"

        def __add_count(kvs, item):
            result = item._item.copy()
            result[arg] = 1
            return result

        return self.__new_group(converter=__add_count)

    def count(self, arg, **kwargs):
        if not arg:
            arg = "count"

        def __count(kvs, l):
            keys = []
            values = []
            for k, v in kvs:
                keys.append(k)
                values.append(v)
            keys.append(arg)
            values.append(len(l))
            return SequenceDict(keys, values)

        return self.__new_group(l_converter=__count)

    def sum(self, arg, error, **kwargs):
        if not arg:
            error("No argument given")
        sum_keys = arg.split()

        def __sum(kvs, l):
            keys = []
            values = []
            for k, v in kvs:
                keys.append(k)
                values.append(v)
            keys.extend(sum_keys)
            for key in sum_keys:
                val = 0
                for item in l:
                    val += item[key]
                values.append(val)
            return SequenceDict(keys, values)

        return self.__new_group(l_converter=__sum)


# --- command.py ---

__commands = {}


def command(name):
    def __decor(func):
        __commands[name] = func
        return func

    return __decor


def execute(name, **kwargs):
    if name not in __commands:
        raise Error("Command '{}' not found".format(name))
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
        return OpenedFile(arg)
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
    console.output("")
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
@command("group")
@command("un-group")
@command("sort")
@command("count")
@command("add-count")
@command("sum")
@command("rename")
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


# --- main.py ---

class Console(object):
    def __init__(self):
        clear_screen()
        self.result = None
        self.stored_values = {}

    def single_line(self, line):
        if not line:
            return
        try:
            cmd, arg = line.split(None, 1)
        except ValueError:
            cmd, arg = line, None
        self.result = execute(
            cmd,
            arg=arg,
            last=self.result,
            console=self,
            error=self.error
        )

    def line(self, line):
        MultiLineGroup(line).execute(self)

    def exit(self):
        raise ExitCommand

    def reset(self):
        raise ResetCommand

    def error(self, message):
        raise Error(message)

    def output(self, message):
        print(message)

    def message(self, message):
        print("\033[1;32m" + message + "\033[0m")

    def print(self):
        if self.result is not None:
            print("\033[1;36m" + repr(self.result) + "\033[0m")


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
        except Error as e:
            print("\033[1;31m" + e.msg + "\033[0m")
        except Exception as e:
            print("\033[1;31mUnhandled exception: {}\033[0m".format(e))


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
            line = input("> ")
            console.line(line)
        except ResetCommand:
            console = Console()
            continue
        except ExitCommand:
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
