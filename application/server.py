import logging
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
import select
import argparse
import sys
from server_database import Storage
import threading

from common.utils import send_message, get_message
import log.server_log_config
from deco import log
import descriptors as dpts
from metaclasses import ServerMetaclass

LOG = logging.getLogger("server_logger")

class Server(threading.Thread, metaclass=ServerMetaclass):
	addr = dpts.Address()
	port = dpts.Port()

	def __init__(self, addr, port, database):
		super().__init__()
		self.addr, self.port = addr, port
		self.sock = self.create_listening_socket(self.addr, self.port)

		self.all_client_sockets = []
		self.messages_list = []
		self.usernames_sockets_dict = {}

		self.database = database
		print(f"Server launched at: {self.addr}:{self.port}")

	def run(self):
		while True:
			try:
				self.client_sock, self.client_addr = self.sock.accept()
			except OSError:
				pass
			else:
				self.all_client_sockets.append(self.client_sock)
				LOG.info(f"Client connection registered from: {self.client_addr[0]}:{self.client_addr[1]}")

			self.recv_list = []
			self.write_list = []
			self.error_list = []
			try:
				if self.all_client_sockets:
					self.recv_list, self.write_list, self.error_list = select.select(self.all_client_sockets, self.all_client_sockets, [], 0)
			except OSError:
				pass

			if self.recv_list:
				for client in self.recv_list:
					try:
						self.process_client_message(get_message(client), self.messages_list, client, self.all_client_sockets,
											   self.usernames_sockets_dict)
					except:
						LOG.info(f"Client {client.getpeername()} disconnected from server")
						self.all_client_sockets.remove(client)

			for msg in self.messages_list:
				try:
					self.send_ptp_message(msg, self.usernames_sockets_dict, self.write_list)
				except:
					LOG.info(f"Client {msg[vrb.TO]} disconnected from server")
					self.all_client_sockets.remove(self.usernames_sockets_dict[vrb.TO])
					del self.usernames_sockets_dict[msg[vrb.TO]]
			self.messages_list.clear()

	def create_listening_socket(self, adr, port):
		sock = socket(AF_INET, SOCK_STREAM)
		sock.bind((adr, port))
		sock.listen(vrb.MAX_CONNECTIONS)
		sock.settimeout(0.3)
		LOG.info(f"Socket created and listening: {adr}:{port}")
		return sock

	@log
	def process_client_message(self, message, message_list, client, all_clients, clients_sockets):
		if vrb.ACTION in message and message[vrb.ACTION] == vrb.PRESENCE and vrb.TIME in message \
				and vrb.USER in message:
			if message[vrb.USER][vrb.ACCOUNT_NAME] not in clients_sockets.keys():
				clients_sockets[message[vrb.USER][vrb.ACCOUNT_NAME]] = client

				client_ip, client_port = client.getpeername()
				print(client_ip, client_port)
				self.database.user_login(message[vrb.USER][vrb.ACCOUNT_NAME], client_ip, client_port)

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
			self.database.user_logout(message[vrb.ACCOUNT_NAME])

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

	def send_ptp_message(self, message, clients_sockets, waiting_clients):
		if message[vrb.TO] in clients_sockets and clients_sockets[message[vrb.TO]] in waiting_clients:
			send_message(clients_sockets[message[vrb.TO]], message)
			LOG.info(f"Message sent to {message[vrb.TO]} from {message[vrb.FROM]}")
		elif message[vrb.TO] in clients_sockets and clients_sockets[message[vrb.TO]] not in waiting_clients:
			raise ConnectionError
		else:
			LOG.error(f"There is no user {message[vrb.TO]} in system.")

def print_help():
	print("List of commands:")
	print("users - known users list")
	print("connected - connected users list")
	print("loghist - user login history")
	print("exit - server sutdown")


def main():
	parser = argparse.ArgumentParser(description="Server launch")
	parser.add_argument("-a", "--address", nargs="?", default=vrb.DEFAULT_IP_ADDRESS, help="Server ip address")
	parser.add_argument("-p", "--port", nargs="?", default=vrb.DEFAULT_PORT, help="Server port")
	arguments = parser.parse_args(sys.argv[1:])
	adr = arguments.address
	port = arguments.port

	database = Storage()

	if 1023 > port > 65536:
		LOG.critical(f"Wrong port: {port}")
		raise ValueError

	server = Server(adr, port, database)

	server.start()

	while True:
		command = input("Input command: ")
		if command == "help":
			print_help()
		elif command == "exit":
			break
		elif command == "users":
			for user in sorted(database.users_list()):
				print(f"User {user[0]}, last login: {user[1]}")
		elif command == "connected":
			for user in sorted(database.active_users_list()):
				print(f"User {user[0]}, connected: {user[1]}:{user[2]}, login time: {user[3]}")
		elif command == "loghist":
			name = input(
				"Input username to view user's history, or press enter to view global history: ")
			for user in sorted(database.login_history(name)):
				print(f"User: {user[0]} login time: {user[1]}. Login from: {user[2]}:{user[3]}")
		else:
			print("Unknown command")
		print("--------------------------------")


if __name__ == "__main__":
	main()
