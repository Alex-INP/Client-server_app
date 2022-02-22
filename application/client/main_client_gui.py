import base64
import datetime
import logging
import sys
import threading
import time

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from PyQt5 import QtCore
from PyQt5.QtGui import QBrush, QColor, QFont
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QApplication, QMessageBox
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

from application.client.client_gui import Ui_MainWindow
import application.common.variables as vrb
from application.common.utils import send_message

LOG = logging.getLogger("client_logger")
SOCKET_LOCK = threading.Lock()

class MainWindow(QMainWindow):
	def __init__(self, sock, database, msg_queue, add_contact_gui, username=""):
		super(MainWindow, self).__init__()
		self.username = username
		self.password = ""
		self.database = database
		self.current_target_username = ""
		self.msg_queue = msg_queue
		self.add_contact_gui = add_contact_gui
		self.sock = sock
		self.user_decrypter = None
		self.target_encryptor = None

		self.message_box = QMessageBox()

		self.interface = Ui_MainWindow()
		self.interface.setupUi(self)
		self.setFixedSize(810, 639)

		self.interface.contactsLabel.setFont(QFont("Calibri", 15))

		self.interface.chatList.horizontalHeader().hide()
		self.interface.chatList.verticalHeader().hide()
		self.interface.chatList.setColumnCount(1)
		self.interface.chatList.setRowCount(1)
		self.interface.chatList.setColumnWidth(0, 491)

		self.item = QTableWidgetItem("History Start")
		self.item.setTextAlignment(Qt.AlignCenter)
		self.item.setFont(QFont("Calibri", 13))
		self.interface.chatList.setItem(0, 0, self.item)

		self.interface.addContactButton.clicked.connect(self.show_add_contact_gui)
		self.interface.deleteContactButton.clicked.connect(self.delete_contact)
		self.interface.sendButton.clicked.connect(self.send_client_message)

		self.interface.lineEdit.setAlignment(Qt.AlignTop)

	def send_client_message(self):
		msg_text = self.interface.lineEdit.text()
		self.interface.lineEdit.clear()

		if self.current_target_username:
			all_data = [vrb.MESSAGE, self.username, self.current_target_username, msg_text, time.time()]
			self.create_n_send_message(self.sock, *all_data)

			self.msg_queue.put(all_data)

	def show_add_contact_gui(self):
		self.add_contact_gui.show()

	def check_chat_length(self):
		if self.interface.chatList.rowCount() >= 10:
			self.interface.chatList.setColumnWidth(0, 473)

	def add_item_to_chat(self, item_data):
		sender, recipient, message, date = item_data
		position = self.interface.chatList.rowCount()

		self.interface.chatList.insertRow(position)

		if sender == self.username:
			item = QTableWidgetItem(
				f"{date.strftime('%m-%d-%Y %H:%M:%S')} Your message to {recipient}:\n{message}"
			)
			item.setFont(QFont("Calibri", 13))
			item.setTextAlignment(Qt.AlignRight)
			item.setForeground(QBrush(QColor(0, 200, 0)))
		else:
			item = QTableWidgetItem(
				f"{date.strftime('%m-%d-%Y %H:%M:%S')} Message from {sender}:\n{message}"
			)
			item.setFont(QFont("Calibri", 13))
			item.setForeground(QBrush(QColor(200, 0, 0)))

		item.setFlags(self.item.flags() & ~QtCore.Qt.ItemIsEditable & ~QtCore.Qt.ItemIsSelectable)
		self.interface.chatList.setItem(position, 0, item)
		self.interface.chatList.resizeRowsToContents()
		self.check_chat_length()
		self.interface.chatList.scrollToBottom()

	def fill_chat_history(self, item):
		target_username = item.text()
		self.current_target_username = target_username

		self.set_current_encryptor()

		history = self.database.get_user_history(self.username, target_username)

		for i in range(1, self.interface.chatList.rowCount()):
			self.interface.chatList.removeRow(1)

		for history_element in history:
			self.add_item_to_chat(history_element)

	def reload_contact_list(self):
		self.interface.contactsList.clear()
		self.interface.contactsList.insertItems(0, self.database.get_user_contacts(self.username))

	@pyqtSlot(dict)
	def show_mainwindow(self, value):
		self.username = value["username"]
		self.password = value["password"]
		self.database.user_create(self.username)
		self.interface.usernameLabel.setText(f"You are: {self.username}")
		self.interface.usernameLabel.setFont(QFont("Calibri", 15))

		self.interface.contactsList.setFont(QFont("Calibri", 16))
		self.reload_contact_list()
		self.interface.contactsList.itemDoubleClicked.connect(self.fill_chat_history)

		self.interface.statusbar.showMessage("Client enabled.")

		self.show()

	@pyqtSlot(str)
	def add_contact(self, value):
		self.database.add_contact(self.username, value)
		self.reload_contact_list()

	def delete_contact(self):
		target_username = self.interface.contactsList.selectedItems()[0].text()
		if target_username == self.current_target_username:
			self.current_target_username = ""
		self.database.delete_contact(self.username, target_username)
		self.reload_contact_list()

	def make_connection_show_mainwindow(self, button_object):
		button_object.ok_username_signal.connect(self.show_mainwindow)

	def make_connection_add_contact(self, button_object):
		button_object.add_contact_signal.connect(self.add_contact)

	def get_user_login_data(self):
		return [self.username, self.password]

	def message_queue_check(self):
		if self.msg_queue.qsize() > 0:
			message = self.msg_queue.get()

			if message[0] == vrb.MESSAGE:
				message = message[1:]
				message[-1] = datetime.datetime.fromtimestamp(message[-1])
				if self.username == message[0]:
					self.add_item_to_chat(message)
				elif self.current_target_username == message[0]:
					message = self.decrypt_message(message)
					message[2] = message[2].decode()
					self.add_item_to_chat(message)
				elif message[0] not in self.database.get_user_contacts(self.username):
					message = self.decrypt_message(message)
					message[2] = message[2].decode()
					if self.message_box.question(
							self,
							"New message",
							f"{message[0]} send a message for you. Add to contact list?",
							QMessageBox.Yes,
							QMessageBox.No
					) == QMessageBox.Yes:
						self.add_contact(message[0])
					else:
						return

				self.database.new_message_add(*message)
			if message[0] == vrb.RETURN_PUBKEY:
				self.set_current_encryptor(message)

	def decrypt_message(self, data):
		msg = data[2]
		ms_base_64_decoded = base64.b64decode(msg.encode("ascii"))
		try:
			data[2] = self.user_decrypter.decrypt(ms_base_64_decoded)
		except:
			LOG.error("Cannot decrypt message")
			self.show_message_box("Cannot decrypt message")
		return data


	def set_current_encryptor(self, response=None):
		target_public_key = self.database.get_contact_pubkey(self.current_target_username)
		if not target_public_key:
			if response is None:
				send_message(self.sock, {vrb.ACTION: vrb.ASK_PUBKEY, vrb.PUBKEY_OWNER: self.current_target_username})
			else:
				if response[1] == 200:
					target_public_key = response[2]
					self.database.set_contact_pubkey(self.current_target_username, target_public_key)
					key = RSA.import_key(target_public_key)
					self.target_encryptor = PKCS1_OAEP.new(key)
				else:
					LOG.error(f"Wrong server response. No public key in response. Error: {response[2]}")
					self.show_message_box("This user had never logged in.")
					return
		else:
			key = RSA.import_key(target_public_key)
			self.target_encryptor = PKCS1_OAEP.new(key)

	def create_n_send_message(self, sock, jim_msg_var, username, target_username, msg, date):
		enc_msg = self.target_encryptor.encrypt(msg.encode())
		enc_msg_base_64 = base64.b64encode(enc_msg)

		msg_to_server = {
			vrb.ACTION: vrb.MESSAGE,
			vrb.TIME: date,
			vrb.TO: target_username,
			vrb.FROM: username,
			vrb.JIM_ENCODING: vrb.ENCODING,
			vrb.JIM_MESSAGE: enc_msg_base_64.decode("ascii"),
		}
		LOG.info(f"Message from user {username} to server created: {msg_to_server}")
		try:
			send_message(sock, msg_to_server)
			LOG.info("Message sent")
		except:
			LOG.critical("Connection to server lost")
			sys.exit(1)

	def send_exit_message(self, sock):
		send_message(sock, {vrb.ACTION: vrb.EXIT, vrb.TIME: time.time(), vrb.ACCOUNT_NAME: self.username})
		LOG.info("User closed the program.")
		time.sleep(0.5)

	def closeEvent(self, event):
		self.send_exit_message(self.sock)

	def show_message_box(self, text):
		msgBox = QMessageBox()
		msgBox.setIcon(QMessageBox.Information)
		msgBox.setText(text)
		msgBox.setWindowTitle("Message")
		msgBox.setStandardButtons(QMessageBox.Ok)
		msgBox.buttonClicked.connect(msgBox.close)
		msgBox.exec()


class EnterName_dialog(QDialog):
	ok_username_signal = pyqtSignal(dict)

	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setFixedSize(271, 140)
		self.setWindowTitle("Username")

		self.info_label = QLabel("Enter your username", self)
		self.info_label.move(10, 10)
		self.info_label.setFixedSize(240, 15)

		self.username_edit = QLineEdit(self)
		self.username_edit.setFixedSize(250, 20)
		self.username_edit.move(10, 30)

		self.info_pswd_label = QLabel("Enter your password", self)
		self.info_pswd_label.move(10, 55)
		self.info_pswd_label.setFixedSize(240, 15)

		self.password_edit = QLineEdit(self)
		self.password_edit.setFixedSize(250, 20)
		self.password_edit.move(10, 75)

		self.ok_username = QPushButton("Ok", self)
		self.ok_username.move(10, 105)
		self.ok_username.clicked.connect(self.ok_btn_press)

		self.exit_username = QPushButton("Exit", self)
		self.exit_username.move(185, 105)
		self.exit_username.clicked.connect(sys.exit)

	def ok_btn_press(self):
		username = self.username_edit.text()
		password = self.password_edit.text()
		if username:
			self.ok_username_signal.emit({"username": username, "password": password})
			self.close()


class AddContact_dialog(QDialog):
	add_contact_signal = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		self.setFixedSize(271, 100)
		self.setWindowTitle("Add contact")

		self.info_label = QLabel("Enter Contact username", self)
		self.info_label.move(10, 10)
		self.info_label.setFixedSize(240, 15)

		self.username_edit = QLineEdit(self)
		self.username_edit.setFixedSize(250, 20)
		self.username_edit.move(10, 30)

		self.add_username = QPushButton("Add", self)
		self.add_username.move(10, 70)
		self.add_username.clicked.connect(self.add_contact_btn_press)

		self.exit_addcontact = QPushButton("Exit", self)
		self.exit_addcontact.move(185, 70)
		self.exit_addcontact.clicked.connect(self.no_add)

	def no_add(self):
		self.close()

	def add_contact_btn_press(self):
		username = self.username_edit.text()
		if username:
			self.add_contact_signal.emit(username)
			self.close()



if __name__ == "__main__":
	app = QApplication([])
	gui = EnterName_dialog()
	gui.show()
	app.exec_()

