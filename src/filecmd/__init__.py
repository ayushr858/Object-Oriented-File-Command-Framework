"""
filecmd
=======

A command-driven virtual file system with a modular, object-oriented
design built around the Command pattern.

Sub-packages / modules
-----------------------
vfs        - The in-memory virtual file system (File, Directory, VFS).
commands   - Polymorphic Command implementations (create, delete, copy, move).
history    - Reversible command history providing undo/redo.
parser     - Translates raw text input into Command objects.
cli        - A small REPL that wires parser -> history -> vfs together.
"""

__version__ = "1.0.0"
