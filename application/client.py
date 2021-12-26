from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv

def send_presence(socket_object):
	message = {
		"action": vrb.PRESENCE,
		"time": time.time(),
		"type": "status",
		"user": {
			"account_name": "SomeAccountName",
			"status": "Presence"
		}
	}
	socket_object.send(json.dumps(message).encode(vrb.ENCODING))


def main():
	if "-p" in argv:
		port = int(argv[argv.index('-p') + 1])
	else:
		port = vrb.DEFAULT_PORT
	if "-a" in argv:
		adr = int(argv[argv.index('-a') + 1])
	else:
		adr = vrb.DEFAULT_IP_ADDRESS

	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((adr, port))

	send_presence(sock)
	# sock.send("client message".encode(vrb.ENCODING))

	server_answer = sock.recv(vrb.MAX_PACKAGE_LENGTH)
	print(server_answer.decode(vrb.ENCODING))
	sock.close()


if __name__ == "__main__":
	main()