import logging
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv
from common.utils import send_message, get_message
import log.client_log_config
from deco import log

LOG = logging.getLogger("client_logger")

# def send_presence(socket_object):
# 	message = {
# 		"action": vrb.PRESENCE,
# 		"time": time.time(),
# 		"type": "status",
# 		"user": {
# 			"account_name": "SomeAccountName",
# 			"status": "Presence"
# 		}
# 	}
# 	socket_object.send(json.dumps(message).encode(vrb.ENCODING))

@log
def create_presence(account_name='Guest'):
	result = {
		vrb.ACTION: vrb.PRESENCE,
		vrb.TIME: time.time(),
		vrb.USER: {
			vrb.ACCOUNT_NAME: account_name
		}
	}
	return result

@log
def process_answer(message):
	if vrb.RESPONSE in message:
		LOG.info("Server response content correct")
		if message[vrb.RESPONSE] == 200:
			return '200 : OK'
		return f'400 : {message[vrb.ERROR]}'
	LOG.warning("Incorrect server response content.")
	raise ValueError

def main():
	if "-p" in argv:
		port = int(argv[argv.index('-p') + 1])
	else:
		port = vrb.DEFAULT_PORT
	if "-a" in argv:
		adr = int(argv[argv.index('-a') + 1])
	else:
		adr = vrb.DEFAULT_IP_ADDRESS

	if port <= 1023:
		LOG.critical(f"Wrong port: {port}")
		raise ValueError

	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((adr, port))
	LOG.info(f"Socket created and connected to: {adr}:{port}")

	# send_presence(sock)
	# sock.send("client message".encode(vrb.ENCODING))
	# server_answer = sock.recv(vrb.MAX_PACKAGE_LENGTH)

	message = create_presence()
	send_message(sock, message)
	LOG.info("Presence msg sent")
	server_answer = process_answer(get_message(sock))

	LOG.info(f"Server answer message: {server_answer}")
	sock.close()


if __name__ == "__main__":
	main()
