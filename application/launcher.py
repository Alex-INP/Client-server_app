import subprocess

all_processes = []

while True:
	action = input("Commands list.\nex - exit\nst - start clients and servers\ncl - close all windows\n\nInput command: ")
	if action == "ex":
		break
	elif action == "st":
		all_processes.append(subprocess.Popen("python server.py", creationflags=subprocess.CREATE_NEW_CONSOLE))
		all_processes.append(subprocess.Popen("python client.py -n Viktor", creationflags=subprocess.CREATE_NEW_CONSOLE))
		all_processes.append(subprocess.Popen("python client.py -n Alex", creationflags=subprocess.CREATE_NEW_CONSOLE))
	elif action == "cl":
		while all_processes:
			all_processes.pop().kill()