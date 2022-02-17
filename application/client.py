import logging
import sys
from queue import Queue
from socket import socket, AF_INET, SOCK_STREAM
import time
import argparse
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from application.client.main_client_gui import EnterName_dialog, MainWindow, AddContact_dialog
from application.client_database import ClientStorage
from common.utils import send_message, get_message
import common.variables as vrb
from deco import log
from metaclasses import ClientMetaclass

LOG = logging.getLogger("client_logger")
LOCK = threading.Lock()

def create_client_socket(adr, port):
	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((adr, port))
	LOG.info(f"Socket created and connected to: {adr}:{port}")
	return sock


class Client(threading.Thread, metaclass=ClientMetaclass):
	def __init__(self, sock, main_window_ui_obj, msg_queue, name=""):
		super().__init__()
		self.name = name
		self.main_window_ui_obj = main_window_ui_obj
		self.sock = sock
		self.msg_queue = msg_queue
		self.daemon = True

	def run(self):
		while not self.name:
			self.name = self.main_window_ui_obj.get_username()

		send_message(self.sock, self.create_presence(self.name))
		response = get_message(self.sock)
		LOG.info(f"Presence server response: {response}")

		self.process_message_from_server(self.sock, self.name, self.msg_queue)

	@log
	def create_presence(self, account_name='Guest'):
		result = {
			vrb.ACTION: vrb.PRESENCE,
			vrb.TIME: time.time(),
			vrb.USER: {
				vrb.ACCOUNT_NAME: account_name
			}
		}
		return result


	def process_message_from_server(self, sock, username, msg_queue):
		LOG.debug("Ready to receive messages from server")
		while True:
			try:
				message = get_message(sock)
				if vrb.ACTION in message and message[vrb.ACTION] == vrb.MESSAGE and vrb.TIME in message \
						and vrb.TO in message and message[
					vrb.TO] == username and vrb.FROM in message and vrb.JIM_ENCODING in message \
						and vrb.JIM_MESSAGE in message:
					msg_queue.put([message[vrb.FROM], message[vrb.TO], message[vrb.JIM_MESSAGE], (message[vrb.TIME])])
					LOG.info(f"Message from user: {message[vrb.FROM]}, Message: {message[vrb.JIM_MESSAGE]}")
					print(f"\nMessage from user: {message[vrb.FROM]}\n{message[vrb.JIM_MESSAGE]}")
				else:
					LOG.error(f"Message from server is incorrect: {message}")
			except ConnectionError:
				LOG.critical("Connection to server lost")
				break


def main():
	parser = argparse.ArgumentParser(description="Client launch")
	parser.add_argument("-a", "--address", nargs="?", default=vrb.DEFAULT_IP_ADDRESS, help="Server ip address")
	parser.add_argument("-p", "--port", nargs="?", default=vrb.DEFAULT_PORT, help="Server port")
	parser.add_argument("-n", "--name", nargs="?", default=None, help="Username")
	arguments = parser.parse_args(sys.argv[1:])
	adr = arguments.address
	port = arguments.port
	name = arguments.name

	if 1023 > port >= 65536:
		LOG.critical(f"Wrong port: {port}")
		sys.exit(1)

	try:
		client_socket = create_client_socket(adr, port)
	except (ConnectionRefusedError, ConnectionError):
		LOG.critical(f"Error connecting to server {adr}:{port}. Connection refused.")
		sys.exit(1)

	database = ClientStorage()
	incoming_messages = Queue()

	client_app = QApplication(sys.argv)

	enter_uname_gui = EnterName_dialog()
	add_contact_gui = AddContact_dialog()
	main_gui = MainWindow(client_socket, database, incoming_messages, add_contact_gui)

	main_gui.make_connection_show_mainwindow(enter_uname_gui)
	main_gui.make_connection_add_contact(add_contact_gui)

	if not name:
		enter_uname_gui.show()
	else:
		main_gui.show_mainwindow(name)

	client = Client(client_socket, main_gui, incoming_messages)
	client.start()

	timer = QTimer()
	timer.timeout.connect(main_gui.message_queue_check)
	timer.start(1000)

	LOG.info(f"Client launched. Username: {main_gui.get_username()}, Server address: {adr}:{port}")
	client_app.exec_()


if __name__ == "__main__":
	main()
