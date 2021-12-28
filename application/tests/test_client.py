import os
import sys

sys.path.append(os.path.join(os.getcwd(), '..'))

import unittest
import application.common.variables as vrb
from application.client import create_presence, process_answer


class TestClientSide(unittest.TestCase):

	def setUp(self):
		pass

	def test_create_presence(self):
		returned_data = create_presence()
		returned_data[vrb.TIME] = 10.0
		self.assertEqual({vrb.ACTION: vrb.PRESENCE, vrb.TIME: 10.0, vrb.USER: {vrb.ACCOUNT_NAME: "Guest"}}, returned_data)

	def test_process_answer(self):
		returned_data = process_answer({vrb.RESPONSE: 200})
		self.assertEqual("200 : OK", returned_data)

	def test_process_answer_400(self):
		returned_data = process_answer({vrb.RESPONSE: 400, vrb.ERROR: 'Bad Request'})
		self.assertEqual("400 : Bad Request", returned_data)

	def test_process_answer_bad_request(self):
		self.assertRaises(ValueError, process_answer, {})

	def tearDown(self):
		pass
