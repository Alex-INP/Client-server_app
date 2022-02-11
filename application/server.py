import configparser
import os
import logging
from socket import socket, AF_INET, SOCK_STREAM

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import common.variables as vrb
import json
import time
import select
import argparse
import sys

from application.server_gui import MainWindow, gui_create_model, ConfigWindow
from server_database import Storage
import threading

from common.utils import send_message, get_message
import log.server_log_config
from deco import log
import descriptors as dpts
from metaclasses import ServerMetaclass

LOG = logging.getLogger("server_logger")
new_connection = False


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
		global new_connection
		if vrb.ACTION in message and message[vrb.ACTION] == vrb.PRESENCE and vrb.TIME in message \
				and vrb.USER in message:
			if message[vrb.USER][vrb.ACCOUNT_NAME] not in clients_sockets.keys():
				clients_sockets[message[vrb.USER][vrb.ACCOUNT_NAME]] = client

				client_ip, client_port = client.getpeername()
				print(client_ip, client_port)
				self.database.user_login(message[vrb.USER][vrb.ACCOUNT_NAME], client_ip, client_port)
				print("DB done")
				send_message(client, {vrb.RESPONSE: 200})
				print("RESP SENT")
				new_connection = True
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
	conf = configparser.ConfigParser()

	dir_path = os.path.dirname(os.path.realpath(__file__))
	conf.read(f"{dir_path}/{'server.ini'}")

	default_adr = conf["SETTINGS"]["listen_address"]
	default_port = int(conf["SETTINGS"]["default_port"])


	parser = argparse.ArgumentParser(description="Server launch")
	parser.add_argument("-a", "--address", nargs="?", default=default_adr, help="Server ip address")
	parser.add_argument("-p", "--port", nargs="?", default=default_port, help="Server port")
	arguments = parser.parse_args(sys.argv[1:])
	adr = arguments.address
	port = arguments.port


	# database = Storage(os.path.join(conf["SETTINGS"]["database_path"], conf["SETTINGS"]["database_file"]))
	database = Storage()

	if 1023 > port > 65536:
		LOG.critical(f"Wrong port: {port}")
		raise ValueError

	server = Server(adr, port, database)
	server.daemon = True

	server.start()

	app = QApplication(sys.argv)
	main_window = MainWindow()

	main_window.statusBar().showMessage("Server Working")
	main_window.active_clients_table.setModel(gui_create_model(database))
	main_window.active_clients_table.resizeColumnsToContents()
	main_window.active_clients_table.resizeRowsToContents()

	def list_update():
		global new_connection
		if new_connection:
			main_window.active_clients_table.setModel(gui_create_model(database))
			main_window.active_clients_table.resizeColumnsToContents()
			main_window.active_clients_table.resizeRowsToContents()
			new_connection = False

	def server_config():
		global config_window
		config_window = ConfigWindow()
		config_window.db_path.insert(conf["SETTINGS"]["database_path"])
		config_window.db_file.insert(conf["SETTINGS"]["database_file"])
		config_window.port.insert(conf["SETTINGS"]["default_port"])
		config_window.ip.insert(conf["SETTINGS"]["listen_Address"])
		config_window.save_btn.clicked.connect(save_server_config)

	def save_server_config():
		global config_window
		message = QMessageBox()
		conf["SETTINGS"]["database_path"] = config_window.db_path.text()
		conf["SETTINGS"]["database_file"] = config_window.db_file.text()
		try:
			port = int(config_window.port.text())
		except ValueError:
			message.warning(config_window, "Error", "Port must be an integer")
		else:
			conf["SETTINGS"]["listen_Address"] = config_window.ip.text()
			if 1023 < port < 65536:
				conf["SETTINGS"]["default_port"] = str(port)
				print(port)
				with open("server.ini", "w") as file:
					conf.write(file)
					message.information(config_window, "Ok", "Settings saved.")
			else:
				message.warning(config_window, "Error",	"Wrong port")


	timer = QTimer()
	timer.timeout.connect(list_update)
	timer.start(1000)

	main_window.refresh_button.triggered.connect(list_update)
	main_window.config_btn.triggered.connect(server_config)

	app.exec_()

	# while True:
	# 	command = input("Input command: ")
	# 	if command == "help":
	# 		print_help()
	# 	elif command == "exit":
	# 		break
	# 	elif command == "users":
	# 		for user in sorted(database.users_list()):
	# 			print(f"User {user[0]}, last login: {user[1]}")
	# 	elif command == "connected":
	# 		for user in sorted(database.active_users_list()):
	# 			print(f"User {user[0]}, connected: {user[1]}:{user[2]}, login time: {user[3]}")
	# 	elif command == "loghist":
	# 		name = input(
	# 			"Input username to view user's history, or press enter to view global history: ")
	# 		for user in sorted(database.login_history(name)):
	# 			print(f"User: {user[0]} login time: {user[1]}. Login from: {user[2]}:{user[3]}")
	# 	else:
	# 		print("Unknown command")
	# 	print("--------------------------------")


if __name__ == "__main__":
	main()
