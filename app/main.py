import os
import shlex
import subprocess
import sys
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

completer = Autocompleter()
readline.set_completer(completer.complete)
readline.parse_and_bind("tab: complete")


class CommandHandler:
    TYPE_TEMPLATE = "{arg} is a shell builtin"
    TYPES_BUILTIN = {"echo", "type", "exit", "pwd",}

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
    def handle_redirect(command: str) -> bool:
        subprocess.call(command, shell=True)
        return False

    @staticmethod
    def handle_default(command: str) -> bool:
        print(f"{command}: command not found")
        return False

    def handle_command(self, command: str) -> bool:
        if self.is_a_redirect(command):
            return self.handle_redirect(command)
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

            case (command, arg):
                if self.find_executable(command):
                    return self.handle_exec(command, arg)
                return self.handle_default(command)
        return False

def main() -> None:
    """Entry point for the application script"""
    while True:
        sys.stdout.write("$ ")
        user_input = input()

        should_exit = CommandHandler().handle_command(user_input)
        if should_exit:
            break


if __name__ == "__main__":
    main()
