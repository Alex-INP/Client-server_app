import logging
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv
import select

from common.utils import send_message, get_message
import log.server_log_config
from deco import log

LOG = logging.getLogger("server_logger")

@log
def process_client_message(message, message_list, client):
	if vrb.ACTION in message and message[vrb.ACTION] == vrb.PRESENCE and vrb.TIME in message \
			and vrb.USER in message and message[vrb.USER][vrb.ACCOUNT_NAME] == 'Guest':
		send_message(client, {vrb.RESPONSE: 200})
		LOG.info("Client's presence message has been responded ")
		return

	elif vrb.ACTION in message and message[vrb.ACTION] == vrb.MESSAGE and vrb.TIME in message \
			and vrb.TO in message and vrb.FROM in message and vrb.JIM_ENCODING in message \
			and vrb.JIM_MESSAGE in message:
		message_list.append((message[vrb.TO], message[vrb.JIM_MESSAGE]))
		return

	LOG.warning("Incorrect client message content.")
	return {
		vrb.RESPONSE: 400,
		vrb.ERROR: 'Bad Request'
	}

def create_listening_socket(adr, port):
	sock = socket(AF_INET, SOCK_STREAM)
	sock.bind((adr, port))
	sock.listen(vrb.MAX_CONNECTIONS)
	sock.settimeout(0.2)
	LOG.info(f"Socket created and listening: {adr}:{port}")
	return sock

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

	if 1023 > port > 65535:
		LOG.critical(f"Wrong port: {port}")
		raise ValueError

	sock = create_listening_socket(adr, port)

	all_client_sockets = []
	messages_list = []

	while True:
		try:
			client_sock, client_addr = sock.accept()
		except OSError as e:
			pass
		else:
			all_client_sockets.append(client_sock)
			LOG.info(f"Client connection registered from: {client_addr[0]}:{client_addr[1]}")
		finally:
			recv_list = []
			write_list = []
			error_list = []
			try:
				recv_list, write_list, error_list = select.select(all_client_sockets, all_client_sockets, [], 0)
			except Exception as e:
				pass
			# LOG.info(f"Client {client_addr[0]}:{client_addr[1]} disconnected")
			# print(recv_list)
			# print(write_list)
			# print(error_list)
			# print("_____")
			# print(messages_list)

			if recv_list:
				for client in recv_list:
					try:
						process_client_message(get_message(client), messages_list, client)
						# print("Got msg")
						# print("_____")
						# print(messages_list)
					except:
						LOG.info(f"Client {client.getpeername()} disconnected from server")
						all_client_sockets.remove(client)

			if messages_list and write_list:
				mst_for_client = {
					vrb.ACTION: vrb.MESSAGE,
					vrb.TIME: time.time(),
					vrb.TO: "account_name_1",
					vrb.FROM: messages_list[0][0],
					vrb.JIM_ENCODING: vrb.ENCODING,
					vrb.JIM_MESSAGE: messages_list[0][1]
				}
				del messages_list[0]
				for client in write_list:
					try:
						send_message(client, mst_for_client)
						# print("SENT")
					except:
						LOG.info(f"Client {client.getpeername()} disconnected from server")
						all_client_sockets.remove(client)



if __name__ == '__main__':
	main()
