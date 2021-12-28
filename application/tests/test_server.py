import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

import unittest
import application.common.variables as vrb
from application.server import process_client_message

class TestServerSide(unittest.TestCase):
	ok_response = {vrb.RESPONSE: 200}
	error_response = {vrb.RESPONSE: 400, vrb.ERROR: "Bad Request"}

	def setUp(self):
		pass

	def test_process_client_message_ok(self):
		returned_data = process_client_message({vrb.ACTION: vrb.PRESENCE, vrb.TIME: "10.0", vrb.USER: {vrb.ACCOUNT_NAME: "Guest"}})
		self.assertEqual(self.ok_response, returned_data)

	def test_process_client_message_no_element(self):
		returned_data = process_client_message({vrb.ACTION: vrb.PRESENCE, vrb.TIME: "10.0"})
		self.assertEqual(self.error_response, returned_data)

	def test_process_client_message_not_a_guest(self):
		returned_data = process_client_message({vrb.ACTION: vrb.PRESENCE, vrb.TIME: "10.0", vrb.USER: {vrb.ACCOUNT_NAME: "Alex"}})
		self.assertEqual(self.error_response, returned_data)

	def tearDown(self):
		pass