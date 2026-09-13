import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from filecmd.commands import (
    CopyCommand,
    CreateDirectoryCommand,
    CreateFileCommand,
    DeleteCommand,
    MoveCommand,
)
from filecmd.vfs import VirtualFileSystem


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()

    def test_create_file_command_execute_and_undo(self):
        cmd = CreateFileCommand(self.vfs, "/a.txt", "hi")
        cmd.execute()
        self.assertTrue(self.vfs.exists("/a.txt"))
        cmd.undo()
        self.assertFalse(self.vfs.exists("/a.txt"))

    def test_create_directory_command_execute_and_undo(self):
        cmd = CreateDirectoryCommand(self.vfs, "/docs")
        cmd.execute()
        self.assertTrue(self.vfs.exists("/docs"))
        cmd.undo()
        self.assertFalse(self.vfs.exists("/docs"))

    def test_delete_command_roundtrip_preserves_content(self):
        self.vfs.create_file("/a.txt", "important data")
        cmd = DeleteCommand(self.vfs, "/a.txt")
        cmd.execute()
        self.assertFalse(self.vfs.exists("/a.txt"))
        cmd.undo()
        self.assertEqual(self.vfs.read("/a.txt"), "important data")

    def test_copy_command_undo_removes_copy_only(self):
        self.vfs.create_file("/a.txt", "x")
        cmd = CopyCommand(self.vfs, "/a.txt", "/b.txt")
        cmd.execute()
        self.assertTrue(self.vfs.exists("/b.txt"))
        cmd.undo()
        self.assertFalse(self.vfs.exists("/b.txt"))
        self.assertTrue(self.vfs.exists("/a.txt"))

    def test_move_command_undo_moves_back(self):
        self.vfs.create_file("/a.txt", "x")
        cmd = MoveCommand(self.vfs, "/a.txt", "/b.txt")
        cmd.execute()
        self.assertFalse(self.vfs.exists("/a.txt"))
        self.assertTrue(self.vfs.exists("/b.txt"))
        cmd.undo()
        self.assertTrue(self.vfs.exists("/a.txt"))
        self.assertFalse(self.vfs.exists("/b.txt"))

    def test_redo_via_reexecute_after_undo(self):
        cmd = CreateFileCommand(self.vfs, "/a.txt", "x")
        cmd.execute()
        cmd.undo()
        cmd.execute()  # simulates a redo call
        self.assertTrue(self.vfs.exists("/a.txt"))


if __name__ == "__main__":
    unittest.main()
