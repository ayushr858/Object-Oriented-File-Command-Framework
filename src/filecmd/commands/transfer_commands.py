"""
transfer_commands.py

CopyCommand and MoveCommand — commands that relocate/duplicate nodes.
"""

from __future__ import annotations

from filecmd.commands.base import Command
from filecmd.vfs import VirtualFileSystem


class CopyCommand(Command):
    """Copies src -> dst. Undo simply deletes the created copy."""

    def __init__(self, vfs: VirtualFileSystem, src: str, dst: str):
        super().__init__(vfs)
        self.src = src
        self.dst = dst

    def execute(self) -> str:
        self.vfs.copy(self.src, self.dst)
        self._executed = True
        return f"Copied '{self.src}' -> '{self.dst}'"

    def undo(self) -> str:
        self.vfs.delete(self.dst)
        self._executed = False
        return f"Removed '{self.dst}' (undo copy)"

    def __str__(self) -> str:
        return f"copy {self.src} {self.dst}"


class MoveCommand(Command):
    """Moves/renames src -> dst. Undo moves it back."""

    def __init__(self, vfs: VirtualFileSystem, src: str, dst: str):
        super().__init__(vfs)
        self.src = src
        self.dst = dst

    def execute(self) -> str:
        self.vfs.move(self.src, self.dst)
        self._executed = True
        return f"Moved '{self.src}' -> '{self.dst}'"

    def undo(self) -> str:
        self.vfs.move(self.dst, self.src)
        self._executed = False
        return f"Moved '{self.dst}' -> '{self.src}' (undo move)"

    def __str__(self) -> str:
        return f"move {self.src} {self.dst}"
