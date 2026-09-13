"""
history.py
----------

CommandHistory only knows about the `Command` interface (execute/undo) —
it has no idea what a "file" or a "path" is. That decoupling is what makes
undo/redo work uniformly for every command, present and future, without
this module ever changing (Open/Closed Principle).
"""

from __future__ import annotations

from typing import List, Optional

from filecmd.commands.base import Command


class NothingToUndoError(Exception):
    pass


class NothingToRedoError(Exception):
    pass


class CommandHistory:
    """
    Two stacks, classic undo/redo semantics:

    * `do(command)`   -> execute, push to undo stack, clear redo stack.
    * `undo()`         -> pop from undo stack, call .undo(), push to redo stack.
    * `redo()`         -> pop from redo stack, call .execute(), push to undo stack.

    Running a brand-new command after undoing invalidates the redo branch,
    matching the behavior users expect from editors/shells.
    """

    def __init__(self, max_history: Optional[int] = None):
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self.max_history = max_history

    def do(self, command: Command) -> str:
        result = command.execute()
        self._undo_stack.append(command)
        if self.max_history is not None and len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        return result

    def undo(self) -> str:
        if not self._undo_stack:
            raise NothingToUndoError("Nothing to undo")
        command = self._undo_stack.pop()
        result = command.undo()
        self._redo_stack.append(command)
        return result

    def redo(self) -> str:
        if not self._redo_stack:
            raise NothingToRedoError("Nothing to redo")
        command = self._redo_stack.pop()
        result = command.execute()
        self._undo_stack.append(command)
        return result

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def undo_log(self) -> List[str]:
        return [str(c) for c in self._undo_stack]

    def redo_log(self) -> List[str]:
        return [str(c) for c in self._redo_stack]
