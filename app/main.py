import sys


def main():
    # Wait for user input

    while True:
        sys.stdout.write("$ ")
        command = input()
        if command == "exit 0":
            break
        if command.startswith("echo"):
            print(command[5:])
            continue
        if command.startswith("type"):
            value =  command[5:]
            if value == "echo":
                print("echo is a shell builtin")
                continue
            elif value == "exit":
                print("exit is a shell builtin")
                continue
            elif value == "type":
                print("type is a shell builtin")
                continue
            else:
                print(f"{value}: not found")
                continue
        print(f"{command}: command not found")

if __name__ == "__main__":
    main()
