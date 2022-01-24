import logging
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
import select
import argparse
import sys

from common.utils import send_message, get_message
import log.server_log_config
from deco import log

LOG = logging.getLogger("server_logger")


@log
def process_client_message(message, message_list, client, all_clients, clients_sockets):
	if vrb.ACTION in message and message[vrb.ACTION] == vrb.PRESENCE and vrb.TIME in message \
			and vrb.USER in message:
		if message[vrb.USER][vrb.ACCOUNT_NAME] not in clients_sockets.keys():
			clients_sockets[message[vrb.USER][vrb.ACCOUNT_NAME]] = client
			send_message(client, {vrb.RESPONSE: 200})
			LOG.info("Client's presence message has been responded ")
		else:
			send_message(client, {vrb.RESPONSE: 409,
								  vrb.ERROR: f"Connection with username {message[vrb.USER][vrb.ACCOUNT_NAME]} already exists"})
			all_clients.remove(client)
			client.close()
		return

	elif vrb.ACTION in message and message[vrb.ACTION] == vrb.MESSAGE and vrb.TIME in message \
			and vrb.TO in message and vrb.FROM in message and vrb.JIM_ENCODING in message \
			and vrb.JIM_MESSAGE in message:
		message_list.append(message)
		return
	elif vrb.ACTION in message and message[
		vrb.ACTION] == vrb.EXIT and vrb.TIME in message and vrb.ACCOUNT_NAME in message \
			and message[vrb.ACCOUNT_NAME] in clients_sockets.keys():
		all_clients.remove(client)
		del clients_sockets[message[vrb.ACCOUNT_NAME]]
		client.close()
		LOG.info(f"User {message[vrb.ACCOUNT_NAME]} exited.")
		return

	LOG.warning("Incorrect client message content.")
	send_message(client, {
		vrb.RESPONSE: 400,
		vrb.ERROR: 'Bad Request'
	})
	return


def create_listening_socket(adr, port):
	sock = socket(AF_INET, SOCK_STREAM)
	sock.bind((adr, port))
	sock.listen(vrb.MAX_CONNECTIONS)
	sock.settimeout(0.3)
	LOG.info(f"Socket created and listening: {adr}:{port}")
	return sock


def send_ptp_message(message, clients_sockets, waiting_clients):
	if message[vrb.TO] in clients_sockets and clients_sockets[message[vrb.TO]] in waiting_clients:
		send_message(clients_sockets[message[vrb.TO]], message)
		LOG.info(f"Message sent to {message[vrb.TO]} from {message[vrb.FROM]}")
	elif message[vrb.TO] in clients_sockets and clients_sockets[message[vrb.TO]] not in waiting_clients:
		raise ConnectionError
	else:
		LOG.error(f"There is no user {message[vrb.TO]} in system.")


def main():
	parser = argparse.ArgumentParser(description="Server launch")
	parser.add_argument("-a", "--address", nargs="?", default=vrb.DEFAULT_IP_ADDRESS, help="Server ip address")
	parser.add_argument("-p", "--port", nargs="?", default=vrb.DEFAULT_PORT, help="Server port")
	arguments = parser.parse_args(sys.argv[1:])
	adr = arguments.address
	port = arguments.port

	if 1023 > port > 65536:
		LOG.critical(f"Wrong port: {port}")
		raise ValueError

	sock = create_listening_socket(adr, port)

	all_client_sockets = []
	messages_list = []
	usernames_sockets_dict = {}
	print(f"Server launched at: {adr}:{port}")

	while True:
		try:
			client_sock, client_addr = sock.accept()
		except OSError:
			pass
		else:
			all_client_sockets.append(client_sock)
			LOG.info(f"Client connection registered from: {client_addr[0]}:{client_addr[1]}")

		recv_list = []
		write_list = []
		error_list = []
		try:
			if all_client_sockets:
				recv_list, write_list, error_list = select.select(all_client_sockets, all_client_sockets, [], 0)
		except OSError:
			pass

		if recv_list:
			for client in recv_list:
				try:
					process_client_message(get_message(client), messages_list, client, all_client_sockets,
										   usernames_sockets_dict)
				except:
					LOG.info(f"Client {client.getpeername()} disconnected from server")
					all_client_sockets.remove(client)

		for msg in messages_list:
			try:
				send_ptp_message(msg, usernames_sockets_dict, write_list)
			except:
				LOG.info(f"Client {msg[vrb.TO]} disconnected from server")
				all_client_sockets.remove(usernames_sockets_dict[vrb.TO])
				del usernames_sockets_dict[msg[vrb.TO]]
		messages_list.clear()


if __name__ == '__main__':
	main()
