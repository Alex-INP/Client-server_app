"""
Главный модуль серверной стороны. Принимает и отправляет сообщения клиентам.
"""
import binascii
import configparser
import hmac
import os
import logging
from socket import socket, AF_INET, SOCK_STREAM
from random import choice
from string import ascii_lowercase
import json
import select
import argparse
import sys
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from Crypto.PublicKey import RSA

import application.common.variables as vrb
from server_gui import MainWindow, gui_create_model, ConfigWindow, HistoryWindow, create_stat_model, \
    LoginHistoryWindow, create_login_hist_model
from server_database import Storage
from common.utils import send_message, get_message
import descriptors as dpts
from metaclasses import ServerMetaclass
from application.common.deco import log_it
import log.server_log_config

LOG = logging.getLogger("server_logger")
new_connection = False
thr_lock = threading.Lock()


class Server(threading.Thread, metaclass=ServerMetaclass):
    # """
    # Класс-демон, является дочерним классом по потношению к threading.Thread.
    # Реализует логику сервера. Получает сообщения от пользователей, обрабатывает их, высылает ответы,
    # и пересылает сообщения от одних пользователей другим.
    # """

    addr = dpts.Address()
    port = dpts.Port()

    def __init__(self, addr, port, database):
        """
        :param str addr: ip-адрес сервера
        :param int port: порт сервера
        :param Storage database: объект базы данных
        """
        super().__init__()
        self.addr, self.port = addr, port
        self.sock = self.create_listening_socket(self.addr, self.port)

        self.all_client_sockets = []
        self.messages_list = []
        self.usernames_sockets_dict = {}

        self.database = database
        print(f"Server launched at: {self.addr}:{self.port}")

    def run(self):
        """
        Функция запускаемая потоком. Принимает и разбирает сообщения от пользователей в бесконечном цикле.
        Обрабатывает все виды предусмотреных пользовательских сообщений.

        :return: None
        """
        while True:
            try:
                self.client_sock, self.client_addr = self.sock.accept()
            except OSError:
                pass
            else:
                self.all_client_sockets.append(self.client_sock)
                LOG.info(
                    f"Client connection registered from: {self.client_addr[0]}:{self.client_addr[1]}")

            self.recv_list = []
            self.write_list = []
            self.error_list = []
            try:
                if self.all_client_sockets:
                    self.recv_list, self.write_list, self.error_list = select.select(
                        self.all_client_sockets, self.all_client_sockets, [], 0)
            except OSError:
                pass

            if self.recv_list:
                for client in self.recv_list:
                    try:
                        self.process_client_message(
                            get_message(client),
                            self.messages_list,
                            client,
                            self.all_client_sockets,
                            self.usernames_sockets_dict)
                    except BaseException:
                        LOG.info(
                            f"Client {client.getpeername()} disconnected from server")
                        self.all_client_sockets.remove(client)

            for msg in self.messages_list:
                try:
                    self.send_ptp_message(
                        msg, self.usernames_sockets_dict, self.write_list)
                except BaseException:
                    LOG.info(f"Client {msg[vrb.TO]} disconnected from server")
                    self.all_client_sockets.remove(
                        self.usernames_sockets_dict[vrb.TO])
                    del self.usernames_sockets_dict[msg[vrb.TO]]
            self.messages_list.clear()

    @log_it
    def process_client_message(
            self,
            message,
            message_list,
            client,
            all_clients,
            clients_sockets):
        """
        Принимает и обрабатывает клиентские сообщения.
        Проверяет структуру сообщений на верность.
        В случае прхождения проверки отсылает пользователю ответ.
        Если сообщение не верного формата, возвращает пользователю соответстующий код ошибки.

        :param dict message: контент сообщения
        :param list message_list: список всех сообщений пришедших на сервер
        :param socket client: объект сокета клиента
        :param list all_clients: список всех сокетов клиентов принятых сервером
        :param dict clients_sockets: словарь с именами пользователей и соответстующими им сокетами
        :return: None
        """
        global new_connection

        if vrb.ACTION in message and message[vrb.ACTION] == vrb.PRESENCE and vrb.TIME in message \
                and vrb.USER in message:
            if message[vrb.USER][vrb.ACCOUNT_NAME] not in clients_sockets.keys():
                if vrb.PUBLIC_KEY in message[vrb.USER]:
                    self.database.set_public_key(
                        message[vrb.USER][vrb.ACCOUNT_NAME], message[vrb.USER][vrb.PUBLIC_KEY])
                password_message = "".join(
                    [choice(list(ascii_lowercase)) for _ in range(15)])

                send_message(client, {
                    vrb.RESPONSE: 200,
                    vrb.SERVER_PASSWORD_MESSAGE: password_message
                })

                auth_client_response = client.recv(vrb.MAX_PACKAGE_LENGTH)
                json_response = json.loads(auth_client_response)
                user_password_answer = json_response[vrb.USER][vrb.PASSWORD]

                if self.check_password(
                        message[vrb.USER][vrb.ACCOUNT_NAME], user_password_answer, password_message):
                    clients_sockets[message[vrb.USER]
                                    [vrb.ACCOUNT_NAME]] = client
                    client_ip, client_port = client.getpeername()
                    self.database.user_login(
                        message[vrb.USER][vrb.ACCOUNT_NAME], client_ip, client_port)
                    with thr_lock:
                        new_connection = True
                    LOG.info(
                        f"Client's presence message has been responded. {message[vrb.USER][vrb.ACCOUNT_NAME]} login success.")
                else:
                    client.close()
                    LOG.info(
                        f"{message[vrb.USER][vrb.ACCOUNT_NAME]} login fail.")
            else:
                send_message(
                    client, {
                        vrb.RESPONSE: 409, vrb.ERROR: f"Connection with username {message[vrb.USER][vrb.ACCOUNT_NAME]} already exists"})
                all_clients.remove(client)
                client.close()
            return

        if vrb.ACTION in message and message[vrb.ACTION] == vrb.ASK_PUBKEY and vrb.PUBKEY_OWNER in message:
            target_username = message[vrb.PUBKEY_OWNER]
            public_key = self.database.get_public_key(target_username)
            print(f"PUBKEY ASKED OF {target_username}")
            if public_key:
                send_message(client,
                             {vrb.ACTION: vrb.RETURN_PUBKEY,
                              vrb.RESPONSE: 200,
                              vrb.TARGET_USER_PUBKEY: public_key})
                return

            send_message(client,
                         {vrb.ACTION: vrb.RETURN_PUBKEY,
                          vrb.RESPONSE: 204,
                          vrb.ERROR: "No Content"})
            return

        if vrb.ACTION in message and message[vrb.ACTION] == vrb.MESSAGE and vrb.TIME in message \
                and vrb.TO in message and vrb.FROM in message and vrb.JIM_ENCODING in message \
                and vrb.JIM_MESSAGE in message:
            if message[vrb.TO] in clients_sockets.keys():
                self.database.process_message(
                    message[vrb.FROM], message[vrb.TO])
            message_list.append(message)
            return

        if vrb.ACTION in message and message[
            vrb.ACTION] == vrb.EXIT and vrb.TIME in message and vrb.ACCOUNT_NAME in message \
                and message[vrb.ACCOUNT_NAME] in clients_sockets.keys():
            self.database.user_logout(message[vrb.ACCOUNT_NAME])

            all_clients.remove(client)
            del clients_sockets[message[vrb.ACCOUNT_NAME]]
            client.close()

            with thr_lock:
                new_connection = True
            LOG.info(f"User {message[vrb.ACCOUNT_NAME]} exited.")
            return

        LOG.warning("Incorrect client message content.")
        send_message(client, {
            vrb.RESPONSE: 400,
            vrb.ERROR: "Bad Request"
        })
        return

    def create_listening_socket(self, adr, port):
        """
        Создает и возвращает сокет с заданным адресом и портом.
        Также переводит его в режим прослушивания.

        :param str adr: ip-адрес сервера
        :param int port: порт сервера
        :return: объект сокета
        """

        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind((adr, port))
        sock.listen(vrb.MAX_CONNECTIONS)
        sock.settimeout(0.3)
        LOG.info(f"Socket created and listening: {adr}:{port}")
        return sock

    def send_ptp_message(self, message, clients_sockets, waiting_clients):
        """
        Пересылает сообщения которые были отправлены одним клиентом и адресованы другому.

        :param dict message: контент сообщения
        :param dict clients_sockets: словарь с именами пользователей и соответстующими им сокетами
        :param list waiting_clients: список клиентских сокетов ожидающих получения сообщения
        :return: None
        """
        if message[vrb.TO] in clients_sockets and clients_sockets[message[vrb.TO]
                                                                  ] in waiting_clients:
            send_message(clients_sockets[message[vrb.TO]], message)
            LOG.info(
                f"Message sent to {message[vrb.TO]} from {message[vrb.FROM]}")
        elif message[vrb.TO] in clients_sockets and clients_sockets[message[vrb.TO]] not in waiting_clients:
            raise ConnectionError
        else:
            LOG.error(f"There is no user {message[vrb.TO]} in system.")

    def check_password(self, username, user_password_answer, password_message):
        """
        Проверяет соответствие пароля пользователя и хранящегося на сервере пароля.

        :param str username: имя пользователя
        :param str user_password_answer: digest присланый пользователем
        :param str password_message: случайное сообщение для проверки пароля
        :return:
        """
        db_password = self.database.get_password_hash(username)
        db_result = hmac.new(
            db_password,
            password_message.encode(),
            "MD5").digest()
        result = hmac.compare_digest(
            binascii.b2a_base64(db_result).decode("ascii").encode("ascii"),
            user_password_answer.encode("ascii"))
        return result


def main():
    """
    Главная управляющая функция серверной стороны.
    Осуществляет стартовую инициализацию необходимых параметров.
    Парсит аргументы запуска, если они есть.
    Проверяет валидность порта. Инициализирует базу данных и создает экземпляры классов,
    ответственных за интерфейс, и осуществляет запуск интерфейса. Активирует поток ответственный за
    обмен сообщениями и их анализ.

    :return: None
    """
    conf = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    conf.read(f"{dir_path}/{'server.ini'}")

    default_port = int(conf["SETTINGS"]["default_port"])

    parser = argparse.ArgumentParser(description="Server launch")
    parser.add_argument(
        "-a",
        "--address",
        nargs="?",
        default=vrb.DEFAULT_IP_ADDRESS,
        help="Server ip address")
    parser.add_argument(
        "-p",
        "--port",
        nargs="?",
        default=default_port,
        help="Server port")
    arguments = parser.parse_args(sys.argv[1:])
    adr = arguments.address
    port = arguments.port

    database = Storage(
        os.path.join(
            conf["SETTINGS"]["database_path"],
            conf["SETTINGS"]["database_file"]))

    if 1023 > port > 65536:
        LOG.critical(f"Wrong port: {port}")
        raise ValueError

    server = Server(adr, port, database)
    server.daemon = True

    server.start()

    app = QApplication(sys.argv)
    main_window = MainWindow(database)

    main_window.statusBar().showMessage("Server Working")
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def list_update():
        """
        Обновляет список подключенных к серверу в данный момент пользователей в окне интерфейса.

        :return: None
        """
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with thr_lock:
                new_connection = False

    def server_config():
        """
        Отображает интерфейс для манипуляции настроек сервера.

        :return: None
        """
        global config_window
        config_window = ConfigWindow()
        config_window.db_path.insert(conf["SETTINGS"]["database_path"])
        config_window.db_file.insert(conf["SETTINGS"]["database_file"])
        config_window.port.insert(conf["SETTINGS"]["default_port"])
        config_window.ip.insert(conf["SETTINGS"]["listen_Address"])
        config_window.save_btn.clicked.connect(save_server_config)

    def save_server_config():
        """
        Сохраняет заданные настройки сервера.

        :return: None
        """
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
                with open("server.ini", "w", encoding="utf-8") as file:
                    conf.write(file)
                    message.information(config_window, "Ok", "Settings saved.")
            else:
                message.warning(config_window, "Error", "Wrong port")

    def show_statistics():
        """
        Отображает интерфейс для демонстрации статистики сервера.

        :return: None
        """
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()

    def show_login_history():
        """
        Отображает интерфейс для демонстрации истории логинов пользователей.

        :return: None
        """
        global hist_window
        hist_window = LoginHistoryWindow()
        hist_window.history_table.setModel(create_login_hist_model(database))
        hist_window.history_table.resizeColumnsToContents()
        hist_window.history_table.resizeRowsToContents()

    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    main_window.refresh_button.triggered.connect(list_update)
    main_window.config_btn.triggered.connect(server_config)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.login_history_btn.triggered.connect(show_login_history)

    app.exec_()


if __name__ == "__main__":
    main()
