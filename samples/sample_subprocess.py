import subprocess

cmd = input("command: ")
subprocess.run(cmd, shell=True)