import logging
import sys
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv
import argparse

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

def create_message():
	msg = input("Input your message: ")
	if msg == "exit":
		sys.exit(1)
	return {
		vrb.ACTION: vrb.MESSAGE,
		vrb.TIME: time.time(),
		vrb.TO: "account_name_1",
		vrb.FROM: "account_name_2",
		vrb.JIM_ENCODING: vrb.ENCODING,
		vrb.JIM_MESSAGE: msg
	}

def client_message_process(message):
	if vrb.ACTION in message and message[vrb.ACTION] == vrb.MESSAGE and vrb.TIME in message \
			and vrb.TO in message and vrb.FROM in message and vrb.JIM_ENCODING in message \
			and vrb.JIM_MESSAGE in message:
		LOG.info(f"Message from user: {message[vrb.FROM]}\nMessage: {message[vrb.JIM_MESSAGE]}")
		print(f"Message from user: {message[vrb.FROM]}\nMessage: {message[vrb.JIM_MESSAGE]}")
		return
	else:
		LOG.error(f"Message from another user is incorrect: {message}")


def main():
	parser = argparse.ArgumentParser(description="Client launch")
	parser.add_argument("-a", "--address", nargs="?", default=vrb.DEFAULT_IP_ADDRESS, help="Server ip adress")
	parser.add_argument("-p", "--port", nargs="?", default=vrb.DEFAULT_PORT, help="Server port")
	parser.add_argument("-m", "--mode", nargs="?", default="listen", help="Client mode")
	arguments = parser.parse_args(sys.argv[1:])
	adr = arguments.address
	port = arguments.port
	mode = arguments.mode


	# if "-p" in argv:
	# 	port = int(argv[argv.index('-p') + 1])
	# else:
	# 	port = vrb.DEFAULT_PORT
	# if "-a" in argv:
	# 	adr = int(argv[argv.index('-a') + 1])
	# else:
	# 	adr = vrb.DEFAULT_IP_ADDRESS

	if 1023 > port > 65535:
		LOG.critical(f"Wrong port: {port}")
		sys.exit(1)

	if mode not in ("listen", "send"):
		LOG.critical(f"Wrong client mode: {mode}")
		sys.exit(1)
	LOG.info(f"Client launched. Mode: {mode}")

	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((adr, port))
	LOG.info(f"Socket created and connected to: {adr}:{port}")
	send_message(sock, create_presence())
	response = get_message(sock)
	LOG.info(f"Presence server response: {response}")

	print(f"Open client mode: {mode}")
	while True:
		if mode == "send":
			try:
				send_message(sock, create_message())
			except:
				LOG.error("Sending message error")
				sys.exit(1)
		if mode == "listen":
			try:
				client_message_process(get_message(sock))
			except ConnectionError:
				LOG.error("Connection error")
				sys.exit(1)



if __name__ == "__main__":
	main()
