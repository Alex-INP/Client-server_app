import logging
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv
from common.utils import send_message, get_message
import log.server_log_config

LOG = logging.getLogger("server_logger")

def process_client_message(message):
	if vrb.ACTION in message and message[vrb.ACTION] == vrb.PRESENCE and vrb.TIME in message \
			and vrb.USER in message and message[vrb.USER][vrb.ACCOUNT_NAME] == 'Guest':
		LOG.info("Client message content correct")
		return {vrb.RESPONSE: 200}

	LOG.warning("Incorrect client message content.")
	return {
		vrb.RESPONSE: 400,
		vrb.ERROR: 'Bad Request'
	}


# def send_status_response(message, client_socket):
# 	message = json.loads(message.decode(vrb.ENCODING))
# 	status_response_msg = {
# 		"response": "",
# 		"time": time.time(),
# 		"alert": ""
# 	}
# 	error_status_response_msg = {
# 		"response": 400,
# 		"error": "Bad request"
# 	}
# 	try:
# 		if message["action"] == 'presence':
# 			status_response_msg["response"] = 200
# 			client_socket.send(json.dumps(status_response_msg).encode(vrb.ENCODING))
# 		else:
# 			client_socket.send(json.dumps(error_status_response_msg).encode(vrb.ENCODING))
# 	except:
# 		client_socket.send(json.dumps(error_status_response_msg).encode(vrb.ENCODING))
# 	client_socket.close()


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
	sock.bind((adr, port))
	sock.listen(vrb.MAX_CONNECTIONS)

	LOG.info(f"Socket created and listening: {adr}:{port}")

	while True:
		client_sock, client_addr = sock.accept()
		LOG.info(f"Client message registered from: {client_addr[0]}:{client_addr[1]}")

		# message = client_sock.recv(vrb.MAX_PACKAGE_LENGTH)
		# send_status_response(message, client_sock)
		try:
			message = get_message(client_sock)
		except:
			LOG.error("Getting message error")
			raise ValueError
		response = process_client_message(message)
		LOG.info(f"Client message content: {message}")

		send_message(client_sock, response)
		LOG.info(f"Response sent.")
		client_sock.close()


	# client_sock.send("server answer message".encode(vrb.ENCODING))
	# client_sock.close()


if __name__ == '__main__':
	main()
