"""
base.py
-------

The Command abstraction that everything else in `commands/` implements.

Design notes
------------
* Every command is *reversible*: `execute()` must leave enough state on
  `self` for `undo()` to restore the file system exactly as it was.
* Commands depend only on the `VirtualFileSystem` primitives, never on each
  other, on the parser, or on the history stack (Dependency Inversion +
  Single Responsibility). That's what lets new commands be added without
  touching parsing or undo/redo logic (Open/Closed).
* `execute()` is called both for the first run *and* for redo, so it must
  be idempotent-safe to call again after an `undo()`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from filecmd.vfs import VirtualFileSystem


class Command(ABC):
    """A single, undoable unit of work against a VirtualFileSystem."""

    def __init__(self, vfs: VirtualFileSystem):
        self.vfs = vfs
        self._executed = False

    @abstractmethod
    def execute(self) -> str:
        """Perform the action. Return a short human-readable result string."""

    @abstractmethod
    def undo(self) -> str:
        """Reverse the action. Return a short human-readable result string."""

    def __str__(self) -> str:  # used by `history` for logging
        return self.__class__.__name__


class CommandError(Exception):
    """Raised by commands for problems that aren't VFS-level errors."""
