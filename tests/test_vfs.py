import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from filecmd.vfs import (
    Directory,
    File,
    PathAlreadyExistsError,
    PathNotFoundError,
    VirtualFileSystem,
)


class TestVirtualFileSystem(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()

    def test_create_and_resolve_file(self):
        self.vfs.create_file("/a.txt", "hello")
        node = self.vfs.resolve("/a.txt")
        self.assertIsInstance(node, File)
        self.assertEqual(node.content, "hello")

    def test_create_nested_directory_and_file(self):
        self.vfs.create_directory("/docs")
        self.vfs.create_file("/docs/notes.txt", "hi")
        self.assertTrue(self.vfs.exists("/docs/notes.txt"))
        listing = self.vfs.list_dir("/docs")
        self.assertEqual([n.name for n in listing], ["notes.txt"])

    def test_create_duplicate_raises(self):
        self.vfs.create_file("/a.txt")
        with self.assertRaises(PathAlreadyExistsError):
            self.vfs.create_file("/a.txt")

    def test_resolve_missing_raises(self):
        with self.assertRaises(PathNotFoundError):
            self.vfs.resolve("/nope.txt")

    def test_delete_and_restore(self):
        self.vfs.create_file("/a.txt", "content")
        entry = self.vfs.delete("/a.txt")
        self.assertFalse(self.vfs.exists("/a.txt"))
        self.vfs.restore(entry)
        self.assertTrue(self.vfs.exists("/a.txt"))
        self.assertEqual(self.vfs.read("/a.txt"), "content")

    def test_delete_directory_removes_subtree(self):
        self.vfs.create_directory("/docs")
        self.vfs.create_file("/docs/a.txt")
        self.vfs.create_file("/docs/b.txt")
        self.vfs.delete("/docs")
        self.assertFalse(self.vfs.exists("/docs"))
        self.assertFalse(self.vfs.exists("/docs/a.txt"))

    def test_copy_file_is_independent(self):
        self.vfs.create_file("/a.txt", "original")
        self.vfs.copy("/a.txt", "/b.txt")
        self.vfs.write("/b.txt", "changed")
        self.assertEqual(self.vfs.read("/a.txt"), "original")
        self.assertEqual(self.vfs.read("/b.txt"), "changed")

    def test_copy_directory_deep_copies_children(self):
        self.vfs.create_directory("/docs")
        self.vfs.create_file("/docs/a.txt", "x")
        self.vfs.copy("/docs", "/docs_copy")
        self.vfs.write("/docs_copy/a.txt", "y")
        self.assertEqual(self.vfs.read("/docs/a.txt"), "x")
        self.assertEqual(self.vfs.read("/docs_copy/a.txt"), "y")

    def test_move_renames_and_relocates(self):
        self.vfs.create_directory("/docs")
        self.vfs.create_file("/a.txt", "content")
        self.vfs.move("/a.txt", "/docs/renamed.txt")
        self.assertFalse(self.vfs.exists("/a.txt"))
        self.assertEqual(self.vfs.read("/docs/renamed.txt"), "content")

    def test_move_into_own_subtree_raises(self):
        self.vfs.create_directory("/docs")
        with self.assertRaises(Exception):
            self.vfs.move("/docs", "/docs/inner")


if __name__ == "__main__":
    unittest.main()
