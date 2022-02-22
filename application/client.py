import binascii
import hashlib
import hmac
import json
import logging
import sys
from queue import Queue
from socket import socket, AF_INET, SOCK_STREAM
import time
import argparse
import threading

from Crypto.Cipher import PKCS1_OAEP
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from Crypto.PublicKey import RSA

from application.client.main_client_gui import EnterName_dialog, MainWindow, AddContact_dialog
from application.client_database import ClientStorage
from common.utils import send_message, get_message
import common.variables as vrb
from deco import log
from metaclasses import ClientMetaclass
from application.log import client_log_config

LOG = logging.getLogger("client_logger")
LOCK = threading.Lock()

def create_client_socket(adr, port):
	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((adr, port))
	LOG.info(f"Socket created and connected to: {adr}:{port}")
	return sock

def send_auth_info(sock, username, password, password_message):
	salt = username.lower()

	pwd = hashlib.pbkdf2_hmac(
		"sha256",
		bytes(password, encoding=vrb.ENCODING),
		bytes(salt, encoding=vrb.ENCODING),
		10000
	)
	pwd = binascii.hexlify(pwd)
	digest = hmac.new(pwd, password_message.encode(), "MD5").digest()
	message = {
			vrb.ACTION: vrb.AUTH,
			vrb.TIME: time.time(),
			vrb.USER: {
				vrb.ACCOUNT_NAME: username,
				vrb.PASSWORD: binascii.b2a_base64(digest).decode("ascii")
			}
		}
	send_message(sock, message)



class Client(threading.Thread, metaclass=ClientMetaclass):
	def __init__(self, sock, main_window_ui_obj, msg_queue, database, name=""):
		super().__init__()
		self.name = name
		self.password = ""
		self.main_window_ui_obj = main_window_ui_obj
		self.sock = sock
		self.msg_queue = msg_queue
		self.daemon = True
		self.database = database
		self.public_key = ""
		self.private_key = ""
		self.decrypter = None

	def run(self):
		while not self.name:
			self.name, self.password = self.main_window_ui_obj.get_user_login_data()

		self.check_private_key()

		self.main_window_ui_obj.user_decrypter = self.decrypter


		if self.public_key != "set on server":
			send_message(self.sock, self.create_presence(self.name, self.public_key.decode('ascii')))
		else:
			send_message(self.sock, self.create_presence(self.name))

		response = get_message(self.sock)
		LOG.info(f"Presence server response: {response}")

		send_auth_info(self.sock, self.name, self.password, response[vrb.SERVER_PASSWORD_MESSAGE])

		self.process_message_from_server(self.sock, self.name, self.msg_queue)

	@log
	def create_presence(self, account_name, public_key=None):
		result = {
			vrb.ACTION: vrb.PRESENCE,
			vrb.TIME: time.time(),
			vrb.USER: {
				vrb.ACCOUNT_NAME: account_name
			}
		}
		if public_key is not None:
			result[vrb.USER][vrb.PUBLIC_KEY] = public_key
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
					to_queue = [vrb.MESSAGE, message[vrb.FROM], message[vrb.TO], message[vrb.JIM_MESSAGE], message[vrb.TIME]]
					msg_queue.put(to_queue)
					LOG.info(f"Message from user: {message[vrb.FROM]}, Message: {message[vrb.JIM_MESSAGE]}")
					print(f"\nMessage from user: {message[vrb.FROM]}\n{message[vrb.JIM_MESSAGE]}")
				else:
					LOG.error(f"Message from server is incorrect: {message}")
				if vrb.ACTION in message and message[vrb.ACTION] == vrb.RETURN_PUBKEY and vrb.RESPONSE in message:
					if vrb.TARGET_USER_PUBKEY in message:
						msg_queue.put([message[vrb.ACTION], message[vrb.RESPONSE], message[vrb.TARGET_USER_PUBKEY]])
					else:
						msg_queue.put([message[vrb.ACTION], message[vrb.RESPONSE], message[vrb.ERROR]])
			except ConnectionError:
				LOG.critical("Connection to server lost")
				break

	def check_private_key(self):
		self.private_key = self.database.get_private_key(self.name)
		if not self.private_key:
			keys = RSA.generate(2048)
			self.private_key = keys.exportKey()
			self.public_key = keys.public_key().exportKey()
			self.database.set_private_key(self.name, self.private_key)
		else:
			self.public_key = "set on server"

		key_to_decrypter = RSA.import_key(self.private_key)
		self.decrypter = PKCS1_OAEP.new(key_to_decrypter)



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

	client = Client(client_socket, main_gui, incoming_messages, database)
	client.start()

	timer = QTimer()
	timer.timeout.connect(main_gui.message_queue_check)
	timer.start(1000)

	LOG.info(f"Client launched. Username: {main_gui.username}, Server address: {adr}:{port}")
	client_app.exec_()


if __name__ == "__main__":
	main()
