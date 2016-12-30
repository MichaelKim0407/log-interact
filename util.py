from mklibpy.terminal import colored_text as colored_text

__author__ = 'Michael'


class ExitCommand(Exception):
    pass


class ResetCommand(Exception):
    pass


class Error(Exception):
    def __init__(self, msg):
        self.msg = msg


def result(text):
    print(colored_text.get_text(text, "cyan"))


def message(text):
    print(colored_text.get_text(text, "green"))


def error(text):
    print(colored_text.get_text(text, "red"))
