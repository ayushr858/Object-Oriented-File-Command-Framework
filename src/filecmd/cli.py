"""
cli.py
------

A minimal REPL. This is the only module that knows about *all* the other
pieces at once — it composes them but contains no file-system or undo
logic itself.

Commands:
    touch <path> [content]     create a file
    mkdir <path>                create a directory
    rm <path>                   delete a file or directory
    cp <src> <dst>               copy
    mv <src> <dst>               move / rename
    ls [path]                   list a directory (default: /)
    cat <path>                  print file contents
    undo                        undo the last command
    redo                        redo the last undone command
    log                         show undo/redo history
    help                        show this message
    exit / quit                 leave the REPL
"""

from __future__ import annotations

from filecmd.commands.base import CommandError
from filecmd.history import CommandHistory, NothingToRedoError, NothingToUndoError
from filecmd.parser import CommandParser, ParseError
from filecmd.vfs import Directory, VfsError, VirtualFileSystem

HELP_TEXT = __doc__.split("Commands:")[1]

_META_COMMANDS = {"undo", "redo", "log", "help", "exit", "quit", "ls", "cat"}


class Repl:
    def __init__(self) -> None:
        self.vfs = VirtualFileSystem()
        self.history = CommandHistory()
        self.parser = CommandParser()
        self.running = True

    def _ls(self, args) -> str:
        path = args[0] if args else "/"
        nodes = self.vfs.list_dir(path)
        if not nodes:
            return "(empty)"
        lines = []
        for node in nodes:
            marker = "/" if isinstance(node, Directory) else ""
            lines.append(f"{node.name}{marker}")
        return "\n".join(lines)

    def _cat(self, args) -> str:
        if not args:
            raise ParseError("'cat' requires a path")
        return self.vfs.read(args[0])

    def handle_line(self, line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return ""

        verb, *rest = stripped.split(maxsplit=1)
        args = rest[0].split() if rest else []
        verb_lower = verb.lower()

        if verb_lower in ("exit", "quit"):
            self.running = False
            return "Goodbye."
        if verb_lower == "help":
            return HELP_TEXT
        if verb_lower == "log":
            undo_log = self.history.undo_log()
            redo_log = self.history.redo_log()
            return (
                f"Undo stack (top last): {undo_log}\n"
                f"Redo stack (top last): {redo_log}"
            )
        if verb_lower == "undo":
            return self.history.undo()
        if verb_lower == "redo":
            return self.history.redo()
        if verb_lower == "ls":
            return self._ls(args)
        if verb_lower == "cat":
            return self._cat(args)

        # anything else goes through parser -> history
        command = self.parser.parse(self.vfs, stripped)
        return self.history.do(command)

    def run(self) -> None:
        print("Object-Oriented File Command Framework. Type 'help' for commands.")
        while self.running:
            try:
                line = input("vfs> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            try:
                output = self.handle_line(line)
                if output:
                    print(output)
            except (ParseError, VfsError, CommandError,
                     NothingToUndoError, NothingToRedoError) as exc:
                print(f"Error: {exc}")


def main() -> None:
    Repl().run()


if __name__ == "__main__":
    main()
