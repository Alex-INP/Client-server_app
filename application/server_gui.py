"""
Отвечает за интерфейс серверной стороны.
Реализует отрисовку и описывает взаимодействие элементов интерфейса.
"""

import binascii
import sys
import hashlib

from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QLabel, QTableView, QDialog, QPushButton, \
    QLineEdit, QFileDialog
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

import common.variables as vrb


def gui_create_model(database):
    """
    Создает и возвращает обьект QStandardItemModel для
    создания таблицы истории сервера.

    :param database: обьект базы данных
    :return: готовый объект таблицы
    """
    list_users = database.active_users_list()
    list_ = QStandardItemModel()
    list_.setHorizontalHeaderLabels(
        ["Client name", "IP address", "Port", "Connection time"])
    for row in list_users:
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list_.appendRow([user, ip, port, time])
    return list_


def create_stat_model(database):
    """
        Создает и возвращает обьект QStandardItemModel для
        создания таблицы истории сообщений сервера.

        :param database: обьект базы данных
        :return: готовый объект таблицы
        """
    hist_list = database.message_history()

    list_ = QStandardItemModel()
    list_.setHorizontalHeaderLabels(
        ["Client name", "Last login time", "Messages sent", "Messages received"])
    for row in hist_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)
        list_.appendRow([user, last_seen, sent, recvd])
    return list_


def create_login_hist_model(database):
    """
    Создает и возвращает обьект QStandardItemModel для создания таблицы истории логинов сервера.

    :param database: обьект базы данных
    :return: готовый объект таблицы
    """
    hist_list = database.login_history()
    list_ = QStandardItemModel()
    list_.setHorizontalHeaderLabels(
        ["Client name", "Login date", "Ip address", "Port"])
    for row in hist_list:
        user, login_date, ip, port = row
        user = QStandardItem(user)
        user.setEditable(False)
        login_date = QStandardItem(str(login_date.replace(microsecond=0)))
        login_date.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        list_.appendRow([user, login_date, ip, port])
    return list_


class MainWindow(QMainWindow):
    """
    Описывает главное окно интерфейса.
    """
    def __init__(self, database):
        super().__init__()
        self.initUI()
        self.database = database

    def initUI(self):
        exitAction = QAction("Exit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.triggered.connect(qApp.quit)

        self.refresh_button = QAction("Update list", self)
        self.config_btn = QAction("Server settings", self)
        self.show_history_button = QAction("Clients message history", self)
        self.login_history_btn = QAction("Clients login history", self)
        self.register_new_user_btn = QAction("Register new user", self)

        self.statusBar()

        self.toolbar = self.addToolBar("MainBar")
        self.toolbar.addAction(exitAction)
        self.toolbar.addAction(self.refresh_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_btn)
        self.toolbar.addAction(self.login_history_btn)
        self.toolbar.addAction(self.register_new_user_btn)

        self.register_new_user_btn.triggered.connect(self.open_register_dialog)

        self.setFixedSize(800, 600)
        self.setWindowTitle("Messaging Server alpha release")

        self.label = QLabel("Connected clients list ", self)
        self.label.setFixedSize(240, 15)
        self.label.move(10, 30)

        self.active_clients_table = QTableView(self)
        self.active_clients_table.move(10, 45)
        self.active_clients_table.setFixedSize(780, 400)

        self.show()

    def open_register_dialog(self):
        """
        Отображает интерфейс окна регистрации нового пользователя.

        :return: None
        """
        global register_win
        register_win = RegisterUser_dialog(self.database)
        register_win.initUI()
        register_win.show()


class ConfigWindow(QDialog):
    """
    Описывает окно настроек сервера.
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setFixedSize(365, 260)
        self.setWindowTitle("Server settings")

        self.db_path_label = QLabel("Database path: ", self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(240, 15)

        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(250, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        self.db_path_select = QPushButton("Browze...", self)
        self.db_path_select.move(275, 28)

        def open_file_dialog():
            """
            Открывает диалоговое окно для выбора директории.

            :return: None
            """
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace("/", "\\")
            self.db_path.clear()
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        self.db_file_label = QLabel("Database name: ", self)
        self.db_file_label.move(10, 68)
        self.db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(150, 20)

        self.port_label = QLabel("Connection port: ", self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(180, 15)

        self.port = QLineEdit(self)
        self.port.move(200, 108)
        self.port.setFixedSize(150, 20)

        self.ip_label = QLabel("Enable connection from IP: ", self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(180, 15)

        self.ip_label_note = QLabel(
            "Leave the field blank to enable connection from all IP's.", self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        self.ip = QLineEdit(self)
        self.ip.move(200, 148)
        self.ip.setFixedSize(150, 20)

        self.save_btn = QPushButton("Save", self)
        self.save_btn.move(190, 220)

        self.close_button = QPushButton("Close", self)
        self.close_button.move(275, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


class HistoryWindow(QDialog):
    """
    Описывает окно истории сервера.
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Client message statistics")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton("Close", self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class LoginHistoryWindow(QDialog):
    """
    Описывает окно истории сообщений сервера.
    """

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Clients login history")
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.close_button = QPushButton("Close", self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class RegisterUser_dialog(QDialog):
    """
    Описывает окно регистрации пользователей сервера.
    """

    def __init__(self, database):
        super().__init__()
        self.initUI()
        self.database = database

    def initUI(self):
        self.setFixedSize(271, 140)
        self.setWindowTitle("Register user")

        self.info_label = QLabel("Enter username", self)
        self.info_label.move(10, 10)
        self.info_label.setFixedSize(240, 15)

        self.username_edit = QLineEdit(self)
        self.username_edit.setFixedSize(250, 20)
        self.username_edit.move(10, 30)

        self.info_pswd_label = QLabel("Enter password", self)
        self.info_pswd_label.move(10, 55)
        self.info_pswd_label.setFixedSize(240, 15)

        self.password_edit = QLineEdit(self)
        self.password_edit.setFixedSize(250, 20)
        self.password_edit.move(10, 75)

        self.ok_register = QPushButton("Register", self)
        self.ok_register.move(10, 105)
        self.ok_register.clicked.connect(self.register_btn_press)

        self.exit_username = QPushButton("Cancel", self)
        self.exit_username.move(185, 105)
        self.exit_username.clicked.connect(self.close_win)

    def close_win(self):
        """
        Закрывает окно регистрации пользователей сервера

        :return: None
        """
        self.close()

    def register_btn_press(self):
        """
        Осуществляет процедуру регистрации нового пользователя.
        Записывает в базу данных его пароль и имя, а также
        закрывает окно регистрации пользователей сервера

        :return: None
        """
        username = self.username_edit.text()
        password = self.password_edit.text()

        if username and password:
            salt = username.lower()

            pwd = hashlib.pbkdf2_hmac(
                "sha256",
                bytes(password, encoding=vrb.ENCODING),
                bytes(salt, encoding=vrb.ENCODING),
                10000
            )
            self.database.create_new_user(username, binascii.hexlify(pwd))
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
