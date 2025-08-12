import os
import shlex
import subprocess
import shutil
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
    def handle_echo(arg: str) -> bool:
        print(f"{" ".join(arg)}")
        return False

    def handle_type(self, arg: str) -> bool:
        arg = "".join(arg)
        if arg in self.TYPES_BUILTIN:
            print(self.TYPE_TEMPLATE.format(arg=arg))
        elif pathname := shutil.which(arg):
            print(pathname)
        else:
            print(f"{arg}: not found")
        return False

    @staticmethod
    def handle_pwd() -> bool:
        print(os.getcwd())
        return False

    @staticmethod
    def handle_exec(command: str, arg: str) -> bool:
        args = [command, *arg]
        subprocess.run(args)
        return False

    @staticmethod
    def handle_cd(arg: str) -> bool:
        arg = Path("".join(arg))
        try:
            os.chdir(arg.expanduser())
        except FileNotFoundError:
            print(f"cd: {arg}: No such file or directory")
        return False

    @staticmethod
    def subprocess_call(command: str) -> bool:
        subprocess.call(command, shell=True)
        return False

    @staticmethod
    def handle_default(command: str) -> bool:
        print(f"{command}: command not found")
        return False

    @staticmethod
    def handle_indexed_history(n) -> bool:
        history_length = readline.get_current_history_length()
        n = int(n)
        for i in range(history_length + 1 - n, history_length + 1):
            print(f"    {i}  {readline.get_history_item(i)}")
        return False

    @staticmethod
    def handle_history() -> bool:
        history_len = readline.get_current_history_length()
        for i in range(1, history_len + 1):
            print(f"    {i}  {readline.get_history_item(i)}")
        return False

    @staticmethod
    def handle_history_from_filename(filename: str) -> bool:
        readline.clear_history()
        readline.add_history(f"history -r {filename}")
        with Path(filename).open("r") as f:
            for line in f:
                readline.add_history(line.strip())
        return False

    @staticmethod
    def write_to_history_file(filename: str) -> bool:
        with Path(filename).open("w") as f:
            for i in range(1, readline.get_current_history_length() + 1):
                f.write(f"{readline.get_history_item(i)}\n")
        return False

    def handle_command(self, command: str) -> bool:
        if self.is_a_redirect(command) or self.is_a_pipe(command):
            return self.subprocess_call(command)
        match self.split_command(command):
            case ("exit", _):
                return True
            case ("echo", arg):
                return self.handle_echo(arg)
            case ("type", arg):
                return self.handle_type(arg)
            case ("pwd", _):
                return self.handle_pwd()
            case ("cd", arg):
                return self.handle_cd(arg)
            case ("history", ["-w", filename]):
                return self.write_to_history_file(filename)
            case ("history", ["-r", filename]):
                return self.handle_history_from_filename(filename)
            case ("history", [arg]):
                return self.handle_indexed_history(arg)
            case ("history", _):
                return self.handle_history()


            case (command, arg):
                if self.find_executable(command):
                    return self.handle_exec(command, arg)
                return self.handle_default(command)
        return False

def main() -> None:
    """Entry point for the application script"""

    handler = CommandHandler()

    while True:
        user_input = input("$ ").strip()
        readline.add_history(user_input)

        should_exit = handler.handle_command(user_input)
        if should_exit:
            break


if __name__ == "__main__":
    main()
