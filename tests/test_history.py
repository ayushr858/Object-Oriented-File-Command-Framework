import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import unittest

from filecmd.commands import CreateFileCommand, DeleteCommand
from filecmd.history import CommandHistory, NothingToRedoError, NothingToUndoError
from filecmd.parser import CommandParser, ParseError
from filecmd.vfs import VirtualFileSystem


class TestCommandHistory(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()
        self.history = CommandHistory()

    def test_do_executes_and_tracks(self):
        self.history.do(CreateFileCommand(self.vfs, "/a.txt"))
        self.assertTrue(self.vfs.exists("/a.txt"))
        self.assertTrue(self.history.can_undo())
        self.assertFalse(self.history.can_redo())

    def test_undo_then_redo_restores_state(self):
        self.history.do(CreateFileCommand(self.vfs, "/a.txt", "hello"))
        self.history.undo()
        self.assertFalse(self.vfs.exists("/a.txt"))
        self.history.redo()
        self.assertTrue(self.vfs.exists("/a.txt"))
        self.assertEqual(self.vfs.read("/a.txt"), "hello")

    def test_new_command_clears_redo_stack(self):
        self.history.do(CreateFileCommand(self.vfs, "/a.txt"))
        self.history.undo()
        self.assertTrue(self.history.can_redo())
        self.history.do(CreateFileCommand(self.vfs, "/b.txt"))
        self.assertFalse(self.history.can_redo())

    def test_multi_step_undo_redo_sequence(self):
        self.history.do(CreateFileCommand(self.vfs, "/a.txt"))
        self.history.do(CreateFileCommand(self.vfs, "/b.txt"))
        self.history.do(DeleteCommand(self.vfs, "/a.txt"))

        self.assertFalse(self.vfs.exists("/a.txt"))
        self.assertTrue(self.vfs.exists("/b.txt"))

        self.history.undo()  # undo delete -> /a.txt back
        self.assertTrue(self.vfs.exists("/a.txt"))

        self.history.undo()  # undo create /b.txt
        self.assertFalse(self.vfs.exists("/b.txt"))

        self.history.undo()  # undo create /a.txt
        self.assertFalse(self.vfs.exists("/a.txt"))

        with self.assertRaises(NothingToUndoError):
            self.history.undo()

        self.history.redo()
        self.history.redo()
        self.history.redo()
        self.assertFalse(self.vfs.exists("/a.txt"))
        self.assertTrue(self.vfs.exists("/b.txt"))

        with self.assertRaises(NothingToRedoError):
            self.history.redo()


class TestCommandParser(unittest.TestCase):
    def setUp(self):
        self.vfs = VirtualFileSystem()
        self.parser = CommandParser()

    def test_parses_touch_with_content(self):
        cmd = self.parser.parse(self.vfs, 'touch /a.txt "hello world"')
        result = cmd.execute()
        self.assertIn("Created file", result)
        self.assertEqual(self.vfs.read("/a.txt"), "hello world")

    def test_parses_mkdir(self):
        cmd = self.parser.parse(self.vfs, "mkdir /docs")
        cmd.execute()
        self.assertTrue(self.vfs.exists("/docs"))

    def test_parses_cp_and_mv_aliases(self):
        self.vfs.create_file("/a.txt", "x")
        self.parser.parse(self.vfs, "cp /a.txt /b.txt").execute()
        self.assertTrue(self.vfs.exists("/b.txt"))
        self.parser.parse(self.vfs, "mv /b.txt /c.txt").execute()
        self.assertTrue(self.vfs.exists("/c.txt"))
        self.assertFalse(self.vfs.exists("/b.txt"))

    def test_unknown_verb_raises(self):
        with self.assertRaises(ParseError):
            self.parser.parse(self.vfs, "frobnicate /a.txt")

    def test_missing_args_raises(self):
        with self.assertRaises(ParseError):
            self.parser.parse(self.vfs, "cp /a.txt")

    def test_custom_verb_can_be_registered(self):
        from filecmd.commands import CreateDirectoryCommand

        self.parser.register("md", lambda vfs, args: CreateDirectoryCommand(vfs, args[0]))
        cmd = self.parser.parse(self.vfs, "md /newdir")
        cmd.execute()
        self.assertTrue(self.vfs.exists("/newdir"))


if __name__ == "__main__":
    unittest.main()
