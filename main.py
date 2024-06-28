from lib_shell import *

def __main__():
    try:
        shell = Shell()
        while True:
            try:
                command = input(shell.prompt)
                if len(command):
                    if command in quit_commands:
                        break
                    else:
                        shell.fetch(command)
            except:
                pass
    except Exception as e:
        print(e)

if __name__ == '__main__':
    __main__()
