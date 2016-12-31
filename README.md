# Interactive Logfile Processor

Author: MichaelKim0407 <jinzheng19930407@sina.com>

# Installation

This Python program requires Python 3 (tested with 3.4+) and does ___not___ run in Python 2.

## Full installation

* Install `mklibpy`. Please refer to https://github.com/MichaelKim0407/mklibpy.

* Clone or download this program.

## Single-file installation

(Under construction)

Download `log-interact-in-one.py`. This file does not require the `mklibpy` package and is executable as long as you have Python 3.

# Usage

## Starting the program

* Run `main.py` or `log-interact-in-one.py` without parameters

    Start the program in interactive mode.

* Run `main.py` or `log-interact-in-one.py` with a parameter

    Execute a script.

    Note that the program will not enter interactive mode, and unsaved results will be lost. If you wish to continue after executing the script, you can enter interactive mode and utilize the `run` command (see below).

## Concepts

Before moving on to `Commands` section, it is important to understand some of the concepts employed in the program.

* File

    A file represents a raw file to be processed.

    * `OpenedFile`

        An opened file ready to be read into memory. After its contents are read, the file will be closed automatically.

* Iterable

    An iterable represents the content of a single log entry.

    * `Line`

        Raw content of a log entry.

    * `SplitLine`

        A log entry split into multiple parts.

    * `Dictionary`

        A log entry in key-value pairs.

* Collection

    A collection represents multiple log entries.

    * `List`

        A collection that is already stored in your computer's memory and ready to be processed.

    * `Iter`

        A collection that is yet to be read from file. This is useful when dealing with large files. You can queue up actions for each log entry before you actually read the file.

## Commands

### Control commands

* `exit`

    Exit the program.

* `reset`

    Restart the program.

* `run SCRIPT`

    * Param `SCRIPT`: The script file to execute

    Execute a script.

### File commands

* `open FILENAME`

    * Param `FILENAME`: The file to be opened
    * Return: `OpenedFile`

    Open a file for reading.

* `close`

    * Execute on: `OpenedFile`
    * Return: `None`

    Close the file. Note that files are automatically closed after reading. However, if you opened a file that you do not want, you should always close it before reading another, as a good habit.

* `read-lines`

    * Execute on: `OpenedFile`
    * Return: `List` or `Iter`

    Read the content of a file, and store it into a `List`. However, if the file is large (i.e. over 1MB), this command will give you a notice and turn into `read-by-line`.

* `read-by-line`

    * Execute on: `OpenedFile`
    * Return: `Iter`

    Return an `Iter` of all lines of the file.

### Iterable commands

Note: All iterable commands can be executed on their collections respectively.

* `split [SEP]`

    * Execute on: `Line` or `SplitLine`
    * Param `SEP` (optional): The separator to split on. If none, all whitespaces and tabs will be considered separators. (see also: `str.split` in Python)
    * Return: `SplitLine`

    Split a line into multiple parts. When executed on a `SplitLine`, each part that has `SEP` will be split.

* `add-before I TEXT`

    * Execute on: `SplitLine`
    * Param `I`: Index starting 0
    * Param `TEXT`: The text to add
    * Return: `SplitLine`

    Add `TEXT` to the start of the `I`th part.

* `add-after I TEXT`

    * Execute on: `SplitLine`
    * Param `I`: Index starting 0
    * Param `TEXT`: The text to add
    * Return: `SplitLine`

    Add `TEXT` to the end of the `I`th part.

* `replace I TEXT1 TEXT2`

    * Execute on: `SplitLine`
    * Param `I`: Index starting 0
    * Param `TEXT1`: The text to be replaced
    * Param `TEXT2`: The text to replace with
    * Return: `SplitLine`

    Replace `TEXT1` with `TEXT2` in the `I`th part.

* `make-dict [SEP]`

    * Execute on: `SplitLine`
    * Param `SEP` (optional):  The separator to split on. If none, all whitespaces and tabs will be considered separators. (see also: `str.split` in Python)
    * Return: `Dictionary`

    Turn each part of a `SplitLine` into a key-value pair, separated by `SEP`. If `SEP` does not exist, the whole part will be considered the key, and the value will be `None` (you should always avoid this: see `add-before`, `add-after` and `replace`)

* `take KEY1 [KEY2...]`

    * Execute on: `Dictionary` or `SplitLine`
    * Param `KEY...`: Keys or indexes
    * Return: Same type as before execution

    Keep only specified keys or indexes.

* `int KEY1 [KEY2...]`

    * Execute on: `Dictionary` or `SplitLine`
    * Param `KEY...`: Keys or indexes
    * Return: Same type as before execution

    Turn the values of specified keys or indexes to integers.

* `number KEY1 [KEY2...]`

    * Execute on: `Dictionary` or `SplitLine`
    * Param `KEY...`: Keys or indexes
    * Return: Same type as before execution

    Turn the values of specified keys or indexes to numbers (floating-point).

### Collection commands

* `print`

    * Execute on: `List`
    * Return: Nothing changed

    Print out the list. A `Line` will be printed without changes; A `SplitLine` will be joined by `^`; A `Dictionary` will be joined by `^` and `=`.

* `save FILENAME`

    * Execute on: `List` or `Iter`
    * Param `FILENAME`: The file to save in
    * Return: `List` -> Nothing changed; `Iter` -> `None`

    Save the content to a file. The format is the same as `print`. When an `Iter` is saved, the file will be read and closed, and nothing will be stored in your computer's memory.

* `do`

    * Execute on: `Iter`
    * Return: `List`

    Execute the iteration. The file will be closed after the operation.

* `abort`

    * Execute on: `Iter`
    * Return: `None`

    Abort the iteration and close the file. This is not necessary, but you should always close files before moving on.

* `store VAR_NAME`

    Under construction.

* `load VAR_NAME`

    Under construction.

* `keep CRITERIA`

    * Execute on: `List` or `Iter` of `Line` or `Dictionary`
    * Param `CRITERIA`: See below
    * Return: Same type as before execution

    When executed on a collection of `Line`, `CRITERIA` should be a regex.

    When executed on a collection of `Dictionary`, `CRITERIA` should be an expression in Python syntax. Keys in the `Dictionary` can be used as variables.

* `throw CRITERIA`

    The opposite of `keep`.

* `limit [START] STOP [STEP]`

    * Execute on: `List` or `Iter`
    * Param `START`, `STOP` and `STEP`: See `range` function in Python.
    * Return: Same type as before execution

    Keep only a number of entries.

* `count [NAME] @ KEY1 [KEY2...]`

    Under construction.

* `sum SUM_KEY1 [SUM_KEY2...] @ KEY1 [KEY2...]`

    Under construction.

## More on commands

* Chaining commands

    Commands can be chained up using `&&` and `;`. This must be done in one line. Just like how you use them in the shell, commands after `&&` will only execute if the command before it returns without errors; commands after `;` will be executed regardless of previous results.

* Error handling

    If a command fails with errors, the previous result will not be overwritten.
