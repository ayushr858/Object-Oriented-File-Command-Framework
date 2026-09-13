"""
vfs.py
------

The storage layer of the framework.

This module knows nothing about commands, parsing, or history — it only
models a file system in memory and exposes primitive, atomic operations
(create, delete, copy, move, read, write). Keeping it ignorant of the rest
of the system is what lets commands/parser/history evolve independently
(Single Responsibility + Dependency Inversion in practice).
"""

from __future__ import annotations

import copy as _copy
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class VfsError(Exception):
    """Base class for all virtual-file-system errors."""


class PathNotFoundError(VfsError):
    def __init__(self, path: str):
        super().__init__(f"No such file or directory: '{path}'")
        self.path = path


class PathAlreadyExistsError(VfsError):
    def __init__(self, path: str):
        super().__init__(f"Path already exists: '{path}'")
        self.path = path


class NotADirectoryErrorVfs(VfsError):
    def __init__(self, path: str):
        super().__init__(f"Not a directory: '{path}'")
        self.path = path


class InvalidPathError(VfsError):
    def __init__(self, path: str, reason: str = ""):
        msg = f"Invalid path: '{path}'"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.path = path


# --------------------------------------------------------------------------- #
# Node hierarchy
# --------------------------------------------------------------------------- #

class Node(ABC):
    """Common base for anything that can live in the tree."""

    def __init__(self, name: str, parent: Optional["Directory"] = None):
        self.name = name
        self.parent = parent

    @abstractmethod
    def clone(self) -> "Node":
        """Return a deep, detached copy of this node (used by copy/undo)."""

    def path(self) -> str:
        if self.parent is None:
            return "/"
        parent_path = self.parent.path()
        sep = "" if parent_path.endswith("/") else "/"
        return f"{parent_path}{sep}{self.name}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.path()!r}>"


class File(Node):
    def __init__(self, name: str, content: str = "", parent: Optional["Directory"] = None):
        super().__init__(name, parent)
        self.content = content

    def clone(self) -> "File":
        return File(self.name, self.content, parent=None)


class Directory(Node):
    def __init__(self, name: str, parent: Optional["Directory"] = None):
        super().__init__(name, parent)
        self.children: Dict[str, Node] = {}

    def clone(self) -> "Directory":
        clone = Directory(self.name, parent=None)
        for child_name, child in self.children.items():
            child_clone = child.clone()
            child_clone.parent = clone
            clone.children[child_name] = child_clone
        return clone

    def add(self, node: Node) -> None:
        node.parent = self
        self.children[node.name] = node

    def remove(self, name: str) -> Node:
        return self.children.pop(name)

    def list(self) -> List[Node]:
        return sorted(self.children.values(), key=lambda n: n.name)


# --------------------------------------------------------------------------- #
# The virtual file system itself
# --------------------------------------------------------------------------- #

@dataclass
class RemovedEntry:
    """Everything needed to put a deleted node back exactly where it was."""
    parent_path: str
    name: str
    node: Node
    index_hint: int = field(default=0)


class VirtualFileSystem:
    """
    An in-memory tree of Files and Directories, addressed by POSIX-like
    absolute paths ("/a/b/c.txt"). All mutation methods are atomic: they
    either fully succeed or raise, never leaving a half-applied change.
    """

    def __init__(self) -> None:
        self.root = Directory("/")

    # ---- path resolution -------------------------------------------------

    @staticmethod
    def _normalize(path: str) -> List[str]:
        if not path or not path.startswith("/"):
            raise InvalidPathError(path, "paths must be absolute, e.g. /a/b.txt")
        parts = [p for p in path.split("/") if p not in ("", ".")]
        return parts

    def resolve(self, path: str) -> Node:
        """Return the node at `path`, or raise PathNotFoundError."""
        parts = self._normalize(path)
        node: Node = self.root
        for part in parts:
            if not isinstance(node, Directory):
                raise NotADirectoryErrorVfs(node.path())
            if part not in node.children:
                raise PathNotFoundError(path)
            node = node.children[part]
        return node

    def exists(self, path: str) -> bool:
        try:
            self.resolve(path)
            return True
        except VfsError:
            return False

    def _resolve_parent(self, path: str) -> "tuple[Directory, str]":
        parts = self._normalize(path)
        if not parts:
            raise InvalidPathError(path, "cannot operate on the root directory")
        *parent_parts, name = parts
        parent: Node = self.root
        for part in parent_parts:
            if not isinstance(parent, Directory) or part not in parent.children:
                raise PathNotFoundError(path)
            parent = parent.children[part]
        if not isinstance(parent, Directory):
            raise NotADirectoryErrorVfs(parent.path())
        return parent, name

    # ---- primitive operations ---------------------------------------------

    def create_file(self, path: str, content: str = "") -> File:
        parent, name = self._resolve_parent(path)
        if name in parent.children:
            raise PathAlreadyExistsError(path)
        file = File(name, content)
        parent.add(file)
        return file

    def create_directory(self, path: str) -> Directory:
        parent, name = self._resolve_parent(path)
        if name in parent.children:
            raise PathAlreadyExistsError(path)
        directory = Directory(name)
        parent.add(directory)
        return directory

    def delete(self, path: str) -> RemovedEntry:
        parent, name = self._resolve_parent(path)
        if name not in parent.children:
            raise PathNotFoundError(path)
        node = parent.remove(name)
        return RemovedEntry(parent_path=parent.path(), name=name, node=node)

    def restore(self, entry: RemovedEntry) -> None:
        """Reinsert a previously removed node — used by undo."""
        parent = self.resolve(entry.parent_path)
        if not isinstance(parent, Directory):
            raise NotADirectoryErrorVfs(entry.parent_path)
        if entry.name in parent.children:
            raise PathAlreadyExistsError(f"{entry.parent_path}/{entry.name}")
        parent.add(entry.node)

    def copy(self, src: str, dst: str) -> Node:
        source = self.resolve(src)
        parent, name = self._resolve_parent(dst)
        if name in parent.children:
            raise PathAlreadyExistsError(dst)
        cloned = source.clone()
        cloned.name = name
        parent.add(cloned)
        return cloned

    def move(self, src: str, dst: str) -> Node:
        if src == dst:
            return self.resolve(src)
        dst_parts = self._normalize(dst)
        src_parts = self._normalize(src)
        if dst_parts[: len(src_parts)] == src_parts and len(dst_parts) > len(src_parts):
            raise InvalidPathError(dst, "cannot move a directory into itself")

        src_parent, src_name = self._resolve_parent(src)
        if src_name not in src_parent.children:
            raise PathNotFoundError(src)
        dst_parent, dst_name = self._resolve_parent(dst)
        if dst_name in dst_parent.children:
            raise PathAlreadyExistsError(dst)

        node = src_parent.remove(src_name)
        node.name = dst_name
        dst_parent.add(node)
        return node

    def read(self, path: str) -> str:
        node = self.resolve(path)
        if not isinstance(node, File):
            raise NotADirectoryErrorVfs(path)  # reusing: "not a file" conceptually
        return node.content

    def write(self, path: str, content: str) -> None:
        node = self.resolve(path)
        if not isinstance(node, File):
            raise VfsError(f"'{path}' is not a file")
        node.content = content

    def list_dir(self, path: str) -> List[Node]:
        node = self.resolve(path)
        if not isinstance(node, Directory):
            raise NotADirectoryErrorVfs(path)
        return node.list()

    def snapshot(self) -> Directory:
        """Deep-copy the whole tree — handy for tests/debugging."""
        return self.root.clone()
