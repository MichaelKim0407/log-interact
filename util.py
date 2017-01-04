from mklibpy.terminal import colored_text as _colored_text

__author__ = 'Michael'


class ExitCommand(Exception):
    pass


class ResetCommand(Exception):
    pass


class Error(Exception):
    def __init__(self, msg):
        self.msg = msg


def result(text):
    print(_colored_text.get_text(text, "cyan"))


def message(text):
    print(_colored_text.get_text(text, "green"))


def error(text):
    print(_colored_text.get_text(text, "red"))


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
