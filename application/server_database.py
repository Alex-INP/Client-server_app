"""
База данных сервера. Создание основных сущностей БД, связей и CRUD операций.
"""

import datetime

import sqlalchemy as sqla
from sqlalchemy.orm import mapper, sessionmaker


class Storage:
    """
    Описывает сущности базы данных, хранит методы, осуществляющие изменения данных таблиц.
    """
    class Users:
        """
        Таблица пользователей.
        """
        def __init__(self, username, password):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None
            self.password = password
            self.public_key = ""

    class ActiveUsers:
        """
        Таблица залогиненых пользователей.
        """
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        """
        Таблица истории логинов.
        """
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date = date
            self.ip_address = ip
            self.port = port

    class UsersMessageHistory:
        """
        Таблица истории сообщений.
        """
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.engine = sqla.create_engine(
            f"sqlite:///{path}",
            echo=False,
            pool_recycle=7200,
            connect_args={"check_same_thread": False}
        )
        self.metadata = sqla.MetaData()

        users_table = sqla.Table(
            "Users", self.metadata, sqla.Column(
                "id", sqla.Integer, primary_key=True), sqla.Column(
                "name", sqla.String, unique=True), sqla.Column(
                "last_login", sqla.DateTime), sqla.Column(
                    "password", sqla.String), sqla.Column(
                        "public_key", sqla.String))
        active_users_table = sqla.Table(
            "Active_users", self.metadata, sqla.Column(
                "id", sqla.Integer, primary_key=True), sqla.Column(
                "user", sqla.ForeignKey("Users.id"), unique=True), sqla.Column(
                "ip_address", sqla.String), sqla.Column(
                    "port", sqla.String), sqla.Column(
                        "login_time", sqla.DateTime))
        login_history = sqla.Table(
            "Login_history", self.metadata, sqla.Column(
                "id", sqla.Integer, primary_key=True), sqla.Column(
                "name", sqla.ForeignKey("Users.id")), sqla.Column(
                "date", sqla.DateTime), sqla.Column(
                    "ip_address", sqla.String), sqla.Column(
                        "port", sqla.String), )
        users_message_history_table = sqla.Table(
            "Message_history", self.metadata, sqla.Column(
                "id", sqla.Integer, primary_key=True), sqla.Column(
                "user", sqla.ForeignKey("Users.id")), sqla.Column(
                "sent", sqla.Integer), sqla.Column(
                    "accepted", sqla.Integer))

        self.metadata.create_all(self.engine)

        mapper(self.Users, users_table)
        mapper(self.ActiveUsers, active_users_table)
        mapper(self.LoginHistory, login_history)
        mapper(self.UsersMessageHistory, users_message_history_table)

        SESSION = sessionmaker(bind=self.engine)
        self.session = SESSION()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def get_password_hash(self, username):
        """
        Возвращает хранящийся хеш пароля, в случае его отсудствия - False.

        :param str username: имя пользователя

        :return:
        """
        query = self.session.query(
            self.Users.password).filter_by(
            name=username).first()
        if query:
            return query[0]
        return False

    def get_public_key(self, username):
        """
        Возвращает хранящийся публичный ключ пользователя,
        в случае его отсудствия - False.

        :param str username: имя пользователя

        :return:
        """
        query = self.session.query(
            self.Users.public_key).filter_by(
            name=username).first()
        if query:
            return query[0]
        return False

    def set_public_key(self, username, key):
        """
        Сохраняет в базу данных новое знаничение публичного ключа пользователя.

        :param str username: имя пользователя
        :param str key: публичный ключ

        :return: None
        """
        user = self.session.query(self.Users).filter_by(name=username).first()
        user.public_key = key
        self.session.commit()

    def create_new_user(self, username, password_hash):
        """
        Сохраняет в базу данных нового пользователя.

        :param str username: имя пользователя
        :param str password_hash: хеш пароля
        :return: None
        """
        query = self.session.query(self.Users).filter_by(name=username)
        if not query.count():
            user = self.Users(username, password_hash)
            self.session.add(user)
            self.session.commit()

            user_msg_history = self.UsersMessageHistory(user.id)
            self.session.add(user_msg_history)
            self.session.commit()

    def get_all_usernames(self):
        """
        Возвращает список имен всех пользователей

        :return: кортеж с именами пользователей
        :rtype: tuple
        """
        return self.session.query(self.Users.name).all()

    def user_login(self, username, ip_address, port):
        """
        Заносит в базу данных факт логина пользователя и всю соответствующую информацию.

        :param str username: имя пользователя
        :param str ip_address: ip-адрес пользователя
        :param str port: порт пользователя
        :return: None
        """
        user = self.session.query(self.Users).filter_by(name=username).first()

        active_user = self.ActiveUsers(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(active_user)

        history = self.LoginHistory(
            user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    def user_logout(self, username):
        """
        Удаляет запись пользователя из таблицы залогиненых пользователей.

        :param str username: имя пользователя
        :return: None
        """
        user = self.session.query(self.Users).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def users_list(self):
        """
        Возвращает список пользователей.

        :return: кортеж с пользователями
        :rtype: tuple
        """
        return self.session.query(self.Users.name, self.Users.last_login).all()

    def active_users_list(self):
        """
        Возвращает список залогиненых пользователей.

        :return: кортеж с залогинеными пользователями
        :rtype: tuple
        """
        query = self.session.query(self.Users.name,
                                   self.ActiveUsers.ip_address,
                                   self.ActiveUsers.port,
                                   self.ActiveUsers.login_time
                                   ).join(self.Users)
        return query.all()

    def login_history(self, username=None):
        """
        Возвращает историю логинов.

        :param str username: имя пользователя
        :return: кортеж с историей логинов
        :rtype: tuple
        """
        query = self.session.query(self.Users.name,
                                   self.LoginHistory.date,
                                   self.LoginHistory.ip_address,
                                   self.LoginHistory.port,
                                   ).join(self.Users)
        if username:
            query = query.filter(self.Users.name == username)
        return query.all()

    def message_history(self):
        """
        Возвращает историю сообщений.

        :return: кортеж с историей сообщений
        :rtype: tuple
        """
        query = self.session.query(
            self.Users.name,
            self.Users.last_login,
            self.UsersMessageHistory.sent,
            self.UsersMessageHistory.accepted
        ).join(self.Users)
        return query.all()

    def process_message(self, sender, recipient):
        """
        Вносит в таблицу факт персылки сообщения от одного пользователя к другому.

        :param str sender: имя пользователя-отправителя
        :param str recipient: имя пользователя-получателя
        :return:
        """
        sender_db_id = self.session.query(
            self.Users).filter_by(
            name=sender).first().id
        recipient_db_id = self.session.query(
            self.Users).filter_by(
            name=recipient).first().id

        sender_row = self.session.query(
            self.UsersMessageHistory).filter_by(
            user=sender_db_id).first()
        sender_row.sent += 1
        recipient_row = self.session.query(
            self.UsersMessageHistory).filter_by(
            user=recipient_db_id).first()
        recipient_row.accepted += 1

        self.session.commit()
