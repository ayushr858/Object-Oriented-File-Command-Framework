"""
file_commands.py

CreateFileCommand, CreateDirectoryCommand, DeleteCommand.

Each command is a thin, polymorphic wrapper around a VFS primitive plus
exactly the state needed to invert it.
"""

from __future__ import annotations

from typing import Optional

from filecmd.commands.base import Command
from filecmd.vfs import RemovedEntry, VirtualFileSystem


class CreateFileCommand(Command):
    def __init__(self, vfs: VirtualFileSystem, path: str, content: str = ""):
        super().__init__(vfs)
        self.path = path
        self.content = content

    def execute(self) -> str:
        self.vfs.create_file(self.path, self.content)
        self._executed = True
        return f"Created file '{self.path}'"

    def undo(self) -> str:
        self.vfs.delete(self.path)
        self._executed = False
        return f"Removed file '{self.path}' (undo create)"

    def __str__(self) -> str:
        return f"create file {self.path}"


class CreateDirectoryCommand(Command):
    def __init__(self, vfs: VirtualFileSystem, path: str):
        super().__init__(vfs)
        self.path = path

    def execute(self) -> str:
        self.vfs.create_directory(self.path)
        self._executed = True
        return f"Created directory '{self.path}'"

    def undo(self) -> str:
        self.vfs.delete(self.path)
        self._executed = False
        return f"Removed directory '{self.path}' (undo create)"

    def __str__(self) -> str:
        return f"create dir {self.path}"


class DeleteCommand(Command):
    """
    Deletes a file or directory (recursively, since directories carry their
    own children). The removed subtree is cached so undo can graft it back
    onto the exact same parent, under the exact same name.
    """

    def __init__(self, vfs: VirtualFileSystem, path: str):
        super().__init__(vfs)
        self.path = path
        self._removed: Optional[RemovedEntry] = None

    def execute(self) -> str:
        self._removed = self.vfs.delete(self.path)
        self._executed = True
        return f"Deleted '{self.path}'"

    def undo(self) -> str:
        if self._removed is None:
            raise RuntimeError("Nothing to undo: command was never executed")
        self.vfs.restore(self._removed)
        self._executed = False
        return f"Restored '{self.path}' (undo delete)"

    def __str__(self) -> str:
        return f"delete {self.path}"
