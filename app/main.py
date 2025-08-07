import os
import subprocess
import sys
import shutil

class CommandHandler:
    TYPE_TEMPLATE = "{arg} is a shell builtin"
    TYPES_BUILTIN = {"echo", "type", "exit",}

    @staticmethod
    def split_command(command: str) -> tuple[str, str]:
        command, _, arg = command.partition(" ")
        return command, arg


    @staticmethod
    def handle_echo(arg: str) -> bool:
        print(arg)
        return False

    def handle_type(self, arg: str) -> bool:
        if arg in self.TYPES_BUILTIN:
            print(self.TYPE_TEMPLATE.format(arg=arg))
        elif pathname := shutil.which(arg):
            print(pathname)
        else:
            print(f"{arg}: not found")
        return False

    @staticmethod
    def find_executable(command: str) -> str | None:
        return shutil.which(command)

    @staticmethod
    def handle_exec(command: str, arg: str) -> bool:
        args = [command, *arg.split(" ")]
        subprocess.run(args)
        return False

    @staticmethod
    def handle_default(command: str) -> bool:
        print(f"{command}: command not found")
        return False

    def handle_command(self, command: str) -> bool:
        match self.split_command(command):
            case ("exit", "0"):
                return True
            case ("echo", arg):
                return self.handle_echo(arg)
            case ("type", arg):
                return self.handle_type(arg)
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
