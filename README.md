# Object-Oriented File Command Framework

A command-driven **virtual file system** with a modular, object-oriented design.
File operations (create, delete, copy, move) are modeled as **polymorphic
commands** using the Command design pattern, giving uniform, extensible
execution plus full **undo/redo** support through reversible command history.

No dependencies — pure Python 3 standard library.

## Why this design

| Concern              | Module                | Responsibility                                             |
|-----------------------|------------------------|-------------------------------------------------------------|
| Storage               | `filecmd/vfs.py`       | In-memory file tree; atomic primitives (create/delete/copy/move/read/write). Knows nothing about commands. |
| Execution unit        | `filecmd/commands/`    | Each operation is a `Command` with `execute()` **and** `undo()`. Depends only on the VFS primitives. |
| History / undo-redo   | `filecmd/history.py`   | Two-stack undo/redo. Only knows the `Command` interface — works for any command, including ones added later. |
| Parsing               | `filecmd/parser.py`    | Turns text into `Command` objects via a factory registry, so new verbs can be added without touching parsing internals. |
| Composition root      | `filecmd/cli.py`       | Wires parser → history → vfs into an interactive REPL. |

This separation is what makes the four SOLID principles concrete here:

- **Single Responsibility** — storage, execution, history, and parsing each live in their own module and change for one reason.
- **Open/Closed** — adding a new command (e.g. `rename`, `symlink`) means adding one class and one factory-registration line; `history.py` and `cli.py` never change.
- **Liskov Substitution** — every command is interchangeable through the `Command` interface (`execute`/`undo`); `CommandHistory` never checks concrete types.
- **Dependency Inversion** — commands and history depend on abstractions (`Command`, `VirtualFileSystem`'s primitive API), not on each other's internals.

## Project layout

```
file-command-framework/
├── main.py                      # entry point: `python main.py`
├── src/filecmd/
│   ├── vfs.py                   # Node / File / Directory / VirtualFileSystem
│   ├── history.py               # CommandHistory (undo/redo stacks)
│   ├── parser.py                # CommandParser + factory registry
│   ├── cli.py                   # interactive REPL
│   └── commands/
│       ├── base.py              # Command ABC
│       ├── file_commands.py     # Create(File|Directory), Delete
│       └── transfer_commands.py # Copy, Move
└── tests/
    ├── test_vfs.py
    ├── test_commands.py
    └── test_history.py
```

## Running it

```bash
python main.py
```

```
vfs> mkdir /docs
Created directory '/docs'
vfs> touch /docs/notes.txt "hello world"
Created file '/docs/notes.txt'
vfs> ls /docs
notes.txt
vfs> cp /docs/notes.txt /docs/notes_copy.txt
Copied '/docs/notes.txt' -> '/docs/notes_copy.txt'
vfs> mv /docs/notes_copy.txt /docs/backup.txt
Moved '/docs/notes_copy.txt' -> '/docs/backup.txt'
vfs> rm /docs/notes.txt
Deleted '/docs/notes.txt'
vfs> undo
Restored '/docs/notes.txt' (undo delete)
vfs> redo
Deleted '/docs/notes.txt'
vfs> log
Undo stack (top last): [...]
Redo stack (top last): []
vfs> exit
Goodbye.
```

### Supported commands

| Verb (aliases)          | Effect                        |
|--------------------------|--------------------------------|
| `touch` / `createfile`   | create a file (optional content) |
| `mkdir` / `createdir`    | create a directory             |
| `rm` / `delete`          | delete a file or directory (recursive) |
| `cp` / `copy`            | copy a file or directory       |
| `mv` / `move`            | move / rename                  |
| `ls [path]`              | list a directory (default `/`) |
| `cat <path>`             | print file contents            |
| `undo`                   | undo the last command          |
| `redo`                   | redo the last undone command   |
| `log`                    | show the undo/redo stacks      |

## Extending the framework

Adding a new operation, e.g. `rename` (a specialized single-path move), takes two steps:

1. Write the command in `filecmd/commands/`:

   ```python
   class RenameCommand(Command):
       def __init__(self, vfs, path, new_name):
           super().__init__(vfs)
           self.path, self.new_name = path, new_name
           self._old_name = None

       def execute(self):
           node = self.vfs.resolve(self.path)
           self._old_name = node.name
           parent_path = self.path.rsplit("/", 1)[0] or "/"
           self.vfs.move(self.path, f"{parent_path}/{self.new_name}")
           return f"Renamed to '{self.new_name}'"

       def undo(self):
           parent_path = self.path.rsplit("/", 1)[0] or "/"
           self.vfs.move(f"{parent_path}/{self.new_name}", self.path)
           return "Renamed back"
   ```

2. Register the verb in `filecmd/parser.py`:

   ```python
   self.register("rename", lambda vfs, args: RenameCommand(vfs, args[0], args[1]))
   ```

`CommandHistory`, the REPL, and every existing test remain untouched.

## Using it as a library

```python
from filecmd.vfs import VirtualFileSystem
from filecmd.commands import CreateFileCommand, DeleteCommand
from filecmd.history import CommandHistory

vfs = VirtualFileSystem()
history = CommandHistory()

history.do(CreateFileCommand(vfs, "/report.txt", "Q3 results"))
history.do(DeleteCommand(vfs, "/report.txt"))

history.undo()  # report.txt is back
print(vfs.read("/report.txt"))  # "Q3 results"
```

## Running the tests

```bash
python -m unittest discover -s tests -v
```

26 tests cover the VFS primitives, each command's execute/undo symmetry,
multi-step undo/redo sequences, and parser behavior (including error paths
and custom-verb registration).

## Possible extensions

- Persist the tree to disk / JSON so state survives restarts.
- A `CompositeCommand` (macro) to group several commands into one undoable step.
- A real POSIX-style shell layer (`cd`, relative paths, wildcards).
- Command logging/serialization for replaying a session.
