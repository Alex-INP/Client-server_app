import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

import unittest
import application.common.variables as vrb
from application.common.utils import get_message, send_message
from socket import socket, AF_INET, SOCK_STREAM


class TestUtils(unittest.TestCase):

	def setUp(self):
		self.serv_socket = socket(AF_INET, SOCK_STREAM)
		self.serv_socket.bind((vrb.DEFAULT_IP_ADDRESS, vrb.DEFAULT_PORT))
		self.serv_socket.listen(vrb.MAX_CONNECTIONS)

		self.client_socket = socket(AF_INET, SOCK_STREAM)
		self.client_socket.connect((vrb.DEFAULT_IP_ADDRESS, vrb.DEFAULT_PORT))

	def test_messaging(self):
		client, address = self.serv_socket.accept()
		send_message(self.client_socket, {"key_1": "val_1"})
		server_response = get_message(client)
		self.assertEqual({"key_1": "val_1"}, server_response)

	def tearDown(self):
		self.serv_socket.close()
		self.client_socket.close()
