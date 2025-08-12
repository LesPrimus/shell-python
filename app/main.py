import os
import shlex
import subprocess
import shutil
from contextlib import suppress
from pathlib import Path
import readline

class Autocompleter:
    available_commands = ("echo", "type", "exit", "pwd", "cd")

    def __init__(self):
        self.options = self.get_options()
        self.matches = []

    def get_options(self):
        options = list(self.available_commands)
        options.extend(self._get_path_executable())
        return options

    @staticmethod
    def _get_path_executable():
        for path in os.environ["PATH"].split(os.pathsep):
            path = Path(path)
            if path.exists():
                for file in path.iterdir():
                    if file.is_file() and shutil.which(file.name):
                        yield file.name

    def complete(self, text, state):
        if state == 0:
            if text:
                self.matches = [option for option in self.options
                                if option.startswith(text)]
            else:
                self.matches = self.options[:]

        # Return match indexed by state
        if state < len(self.matches):
            return f"{self.matches[state]} "
        else:
            return None

    @classmethod
    def complete_hook(cls, substitution, matches, longest_match_length):
        print()
        print(" ".join(matches))
        print("$ " + readline.get_line_buffer(), end="", flush=True)

completer = Autocompleter()
readline.set_completer(completer.complete)
readline.set_completion_display_matches_hook(Autocompleter.complete_hook)
readline.parse_and_bind("tab: complete")
readline.set_auto_history(False)


class CommandHandler:
    TYPE_TEMPLATE = "{arg} is a shell builtin"
    TYPES_BUILTIN = {"echo", "type", "exit", "pwd", "history",}

    def __init__(self):
        self.must_exit = False
        self.last_append_index = 1
        self.load_history_file()

    @staticmethod
    def load_history_file():
        with suppress(OSError):
            if hist_file := os.getenv("HISTFILE"):
                path = Path(hist_file)
                if path.exists():
                    readline.read_history_file(path)

    @staticmethod
    def split_command(command: str) -> tuple[str, str]:
        command, *arg = shlex.split(command)
        return command, arg

    @staticmethod
    def find_executable(command: str) -> str | None:
        return shutil.which(command)

    @staticmethod
    def is_a_redirect(command: str) -> bool:
        return ">" in command or "1>" in command

    @staticmethod
    def is_a_pipe(command: str) -> bool:
        return "|" in command

    @staticmethod
    def handle_echo(arg: str):
        print(f"{" ".join(arg)}")

    def handle_type(self, arg: str):
        arg = "".join(arg)
        if arg in self.TYPES_BUILTIN:
            print(self.TYPE_TEMPLATE.format(arg=arg))
        elif pathname := shutil.which(arg):
            print(pathname)
        else:
            print(f"{arg}: not found")

    @staticmethod
    def handle_pwd():
        print(os.getcwd())

    @staticmethod
    def handle_exec(command: str, arg: str):
        args = [command, *arg]
        subprocess.run(args)

    @staticmethod
    def handle_cd(arg: str):
        arg = Path("".join(arg))
        try:
            os.chdir(arg.expanduser())
        except FileNotFoundError:
            print(f"cd: {arg}: No such file or directory")

    @staticmethod
    def subprocess_call(command: str):
        subprocess.call(command, shell=True)

    @staticmethod
    def handle_default(command: str):
        print(f"{command}: command not found")

    @staticmethod
    def handle_indexed_history(n):
        history_length = readline.get_current_history_length()
        n = int(n)
        for i in range(history_length + 1 - n, history_length + 1):
            print(f"    {i}  {readline.get_history_item(i)}")

    @staticmethod
    def handle_history():
        history_len = readline.get_current_history_length()
        for i in range(1, history_len + 1):
            print(f"    {i}  {readline.get_history_item(i)}")

    @staticmethod
    def handle_history_from_filename(filename: str):
        readline.clear_history()
        readline.add_history(f"history -r {filename}")
        with Path(filename).open("r") as f:
            for line in f:
                readline.add_history(line.strip())

    @staticmethod
    def write_to_history_file(filename: str):
        with Path(filename).open("w") as f:
            for i in range(1, readline.get_current_history_length() + 1):
                f.write(f"{readline.get_history_item(i)}\n")

    def append_to_history(self, filename: str):
        with Path(filename).open("a") as f:
            for i in range(self.last_append_index, readline.get_current_history_length() + 1):
                f.write(f"{readline.get_history_item(i)}\n")
            self.last_append_index = readline.get_current_history_length() + 1


    def handle_command(self, command: str):
        if self.is_a_redirect(command) or self.is_a_pipe(command):
            self.subprocess_call(command)
        else:
            match self.split_command(command):
                case ("exit", _):
                    self.must_exit = True
                case ("echo", arg):
                    self.handle_echo(arg)
                case ("type", arg):
                    self.handle_type(arg)
                case ("pwd", _):
                    self.handle_pwd()
                case ("cd", arg):
                    self.handle_cd(arg)

                # -- History --
                case ("history", ["-a", filename]):
                    self.append_to_history(filename)
                case ("history", ["-w", filename]):
                    self.write_to_history_file(filename)
                case ("history", ["-r", filename]):
                    self.handle_history_from_filename(filename)
                case ("history", [arg]):
                    self.handle_indexed_history(arg)
                case ("history", _):
                    self.handle_history()
                case (command, arg):
                    if self.find_executable(command):
                        self.handle_exec(command, arg)
                    else:
                        self.handle_default(command)

    def run(self):
        while not self.must_exit:
            user_input = input("$ ").strip()
            readline.add_history(user_input)
            self.handle_command(user_input)

if __name__ == "__main__":
    CommandHandler().run()
