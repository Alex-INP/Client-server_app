import logging
import sys
from socket import socket, AF_INET, SOCK_STREAM
import common.variables as vrb
import json
import time
from sys import argv
import argparse
import threading

from common.utils import send_message, get_message
import log.client_log_config
from deco import log
from metaclasses import ClientMetaclass

LOG = logging.getLogger("client_logger")

class Client(metaclass=ClientMetaclass):
	def __init__(self, adr, port, name):
		self.adr, self.port, self.name = adr, port, name

	def run_client(self):
		try:
			self.sock = self.create_client_socket(self.adr, self.port, self.name)
		except (ConnectionRefusedError, ConnectionError):
			LOG.critical(f"Error connecting to server {self.adr}:{self.port}. Connection refused.")
			sys.exit(1)
		else:
			self.receive_thread = threading.Thread(target=self.process_message_from_server, args=(self.sock, self.name), daemon=True)
			self.send_thread = threading.Thread(target=self.user_activity, args=(self.sock, self.name), daemon=True)
			self.receive_thread.start()
			self.send_thread.start()
			LOG.debug("Processes started")
		while True:
			time.sleep(1)
			if self.receive_thread.is_alive() and self.send_thread.is_alive():
				continue
			break

	def create_client_socket(self, adr, port, name):
		sock = socket(AF_INET, SOCK_STREAM)
		sock.connect((adr, port))
		LOG.info(f"Socket created and connected to: {adr}:{port}")
		send_message(sock, self.create_presence(name))
		response = get_message(sock)
		LOG.info(f"Presence server response: {response}")
		return sock

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

	@log
	def process_answer(self, message):
		if vrb.RESPONSE in message:
			LOG.info("Server response content correct")
			if message[vrb.RESPONSE] == 200:
				return '200 : OK'
			return f'400 : {message[vrb.ERROR]}'
		LOG.warning("Incorrect server response content.")
		raise ValueError

	def create_n_send_message(self, sock, username):
		target_username = input("Input receiver's username: ")
		msg = input("Input your message: ")
		msg_to_server = {
			vrb.ACTION: vrb.MESSAGE,
			vrb.TIME: time.time(),
			vrb.TO: target_username,
			vrb.FROM: username,
			vrb.JIM_ENCODING: vrb.ENCODING,
			vrb.JIM_MESSAGE: msg
		}
		LOG.info(f"Message from user {username} to server created: {msg_to_server}")
		try:
			send_message(sock, msg_to_server)
			LOG.info("Message sent")
		except:
			LOG.critical("Connection to server lost")
			sys.exit(1)

	def process_message_from_server(self, sock, username):
		while True:
			try:
				message = get_message(sock)
				if vrb.ACTION in message and message[vrb.ACTION] == vrb.MESSAGE and vrb.TIME in message \
						and vrb.TO in message and message[
					vrb.TO] == username and vrb.FROM in message and vrb.JIM_ENCODING in message \
						and vrb.JIM_MESSAGE in message:
					LOG.info(f"Message from user: {message[vrb.FROM]}, Message: {message[vrb.JIM_MESSAGE]}")
					print(f"\nMessage from user: {message[vrb.FROM]}\n{message[vrb.JIM_MESSAGE]}")
				else:
					LOG.error(f"Message from server is incorrect: {message}")
			except ConnectionError:
				LOG.critical("Connection to server lost")
				break

	def user_activity(self, sock, username):
		print(f"Client launched, your username: {username}")
		print("Available actions.\nms - specify user and send message\ncl - close the program\n\n")

		while True:
			action = input("Input action: ")
			if action == "ms":
				self.create_n_send_message(sock, username)
			elif action == "cl":
				send_message(sock, {vrb.ACTION: vrb.EXIT, vrb.TIME: time.time(), vrb.ACCOUNT_NAME: username})
				print("Closing connection.")
				LOG.info("User closed the program.")
				time.sleep(0.5)
				break
			else:
				print("Unknown command.")


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

	if not name:
		name = input("Input your username: ")
	LOG.info(f"Client launched. Username: {name}, Server address: {adr}:{port}")

	client = Client(adr, port, name)
	client.run_client()


if __name__ == "__main__":
	main()
