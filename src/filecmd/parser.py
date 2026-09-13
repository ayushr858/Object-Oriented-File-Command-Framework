"""
parser.py
---------

Turns a raw text line into a `Command` object. The parser never touches
the VFS directly and never subclasses a command — it only knows the
*shape* of each line (verb + arguments) and delegates construction to a
registry of factory functions.

Adding a new verb (e.g. "rename") means writing one command class and
registering one factory line here — nothing else in the framework needs
to change. That's the Open/Closed principle in action, and it's also why
parsing is unit-testable without ever constructing a VirtualFileSystem.
"""

from __future__ import annotations

import shlex
from typing import Callable, Dict, List

from filecmd.commands import (
    Command,
    CopyCommand,
    CreateDirectoryCommand,
    CreateFileCommand,
    DeleteCommand,
    MoveCommand,
)
from filecmd.vfs import VirtualFileSystem

CommandFactory = Callable[[VirtualFileSystem, List[str]], Command]


class ParseError(Exception):
    pass


def _require_args(verb: str, args: List[str], count: int) -> None:
    if len(args) < count:
        raise ParseError(f"'{verb}' requires {count} argument(s), got {len(args)}")


def _make_create_file(vfs: VirtualFileSystem, args: List[str]) -> Command:
    _require_args("create file", args, 1)
    content = args[1] if len(args) > 1 else ""
    return CreateFileCommand(vfs, args[0], content)


def _make_create_dir(vfs: VirtualFileSystem, args: List[str]) -> Command:
    _require_args("mkdir", args, 1)
    return CreateDirectoryCommand(vfs, args[0])


def _make_delete(vfs: VirtualFileSystem, args: List[str]) -> Command:
    _require_args("delete", args, 1)
    return DeleteCommand(vfs, args[0])


def _make_copy(vfs: VirtualFileSystem, args: List[str]) -> Command:
    _require_args("copy", args, 2)
    return CopyCommand(vfs, args[0], args[1])


def _make_move(vfs: VirtualFileSystem, args: List[str]) -> Command:
    _require_args("move", args, 2)
    return MoveCommand(vfs, args[0], args[1])


class CommandParser:
    """
    Maps a verb (and its aliases) to a factory function. Register custom
    verbs via `register()` to extend the language without editing this
    class's body.
    """

    def __init__(self) -> None:
        self._factories: Dict[str, CommandFactory] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register("touch", _make_create_file)
        self.register("createfile", _make_create_file)
        self.register("mkdir", _make_create_dir)
        self.register("createdir", _make_create_dir)
        self.register("rm", _make_delete)
        self.register("delete", _make_delete)
        self.register("cp", _make_copy)
        self.register("copy", _make_copy)
        self.register("mv", _make_move)
        self.register("move", _make_move)

    def register(self, verb: str, factory: CommandFactory) -> None:
        self._factories[verb.lower()] = factory

    def supported_verbs(self) -> List[str]:
        return sorted(self._factories.keys())

    def parse(self, vfs: VirtualFileSystem, line: str) -> Command:
        line = line.strip()
        if not line:
            raise ParseError("Empty command")

        try:
            tokens = shlex.split(line)
        except ValueError as exc:
            raise ParseError(f"Could not tokenize line: {exc}") from exc

        verb, *args = tokens
        factory = self._factories.get(verb.lower())
        if factory is None:
            raise ParseError(
                f"Unknown command '{verb}'. Supported: {', '.join(self.supported_verbs())}"
            )
        return factory(vfs, args)
