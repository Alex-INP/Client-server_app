from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv

if "-p" in argv:
	port = int(argv[argv.index('-p') + 1])
else:
	port = vrb.DEFAULT_PORT
if "-a" in argv:
	adr = int(argv[argv.index('-a') + 1])
else:
	adr = vrb.DEFAULT_IP_ADDRESS

sock = socket(AF_INET, SOCK_STREAM)
sock.bind((adr, port))
sock.listen(vrb.MAX_CONNECTIONS)


def send_status_response(message, client_socket):
	message = json.loads(message.decode(vrb.ENCODING))
	status_response_msg = {
		"response": "",
		"time": time.time(),
		"alert": ""
	}
	error_status_response_msg = {
		"response": 400,
		"error": "Bad request"
	}
	try:
		if message["action"] == 'presence':
			status_response_msg["response"] = 200
			client_socket.send(json.dumps(status_response_msg).encode(vrb.ENCODING))
		else:
			client_socket.send(json.dumps(error_status_response_msg).encode(vrb.ENCODING))
	except:
		client_socket.send(json.dumps(error_status_response_msg).encode(vrb.ENCODING))
	client_socket.close()


while True:
	client_sock, client_addr = sock.accept()
	message = client_sock.recv(vrb.MAX_PACKAGE_LENGTH)

	send_status_response(message, client_sock)
	print(message.decode(vrb.ENCODING))

	# client_sock.send("server answer message".encode(vrb.ENCODING))
	# client_sock.close()
