"""
База данных клиента. Создание основных сущностей БД, связей и CRUD операций.
"""
from itertools import chain

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

database = declarative_base()


class ClientStorage:
    """
    Описывает сущности базы данных, хранит методы, осуществляющие изменения данных таблиц.
    """
    class Users(database):
        """
        Таблица пользователей.
        """
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        username = Column(String, unique=True)
        private_key = Column(String)

        def __init__(self, username):
            self.username = username
            self.private_key = ""

    class Contacts(database):
        """
        Таблица контактов.
        """
        __tablename__ = "contacts"
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey("users.id"))
        contact_username = Column(String)
        contact_public_key = Column(String)

        def __init__(self, user, contact_username):
            self.user = user
            self.contact_username = contact_username
            self.contact_public_key = ""

    class Messages(database):
        """
        Таблица истории сообщений.
        """
        __tablename__ = "messages"
        id = Column(Integer, primary_key=True)
        sender = Column(String)
        recipient = Column(String)
        message = Column(Text)
        date = Column(DateTime)

        def __init__(self, sender, recipient, message, date):
            self.sender = sender
            self.recipient = recipient
            self.message = message
            self.date = date

    def __init__(self, cl_flag=0):
        if cl_flag != 0:
            db_adr = "client_1_db.db"
        else:
            db_adr = "client_db.db"
        self.engine = create_engine(
            f"sqlite:///{db_adr}",
            echo=False,
            pool_recycle=7200,
            connect_args={
                "check_same_thread": False})
        database.metadata.create_all(self.engine)
        SESSION = sessionmaker(bind=self.engine)
        self.session = SESSION()

    def user_create(self, username):
        """
        Создает пользователя

        :param str username: имя пользователя
        :return: None
        """
        user = self.session.query(self.Users).filter_by(username=username)
        if user.count():
            return
        self.session.add(self.Users(username))
        self.session.commit()

    def set_contact_pubkey(self, contact_username, public_key):
        """
        Сохраняет в базу данных новое знаничение публичного ключа контакта пользователя.

        :param str contact_username: имя пользователя-контакта
        :param str public_key: публичный ключ
        :return: None
        """

        contacts = self.session.query(
            self.Contacts).filter_by(
            contact_username=contact_username)
        for contact in contacts:
            contact.contact_public_key = public_key
        self.session.commit()

    def get_contact_pubkey(self, contact_username):
        """
        Возвращает хранящийся публичный ключ пользователя-контакта,
        в случае его отсудствия - False.

        :param str contact_username: имя пользователя-контакта
        :return:
        """

        query = self.session.query(
            self.Contacts.contact_public_key).filter_by(
            contact_username=contact_username).first()
        if query:
            return query[0]
        return False

    def get_private_key(self, username):
        """
        Возвращает хранящийся приватный ключ пользователя,
        в случае его отсудствия - False.

        :param str username: имя пользователя
        :return:
        """

        query = self.session.query(
            self.Users.private_key).filter_by(
            username=username).first()
        if query:
            return query[0]
        return False

    def set_private_key(self, username, private_key):
        """
        Сохраняет в базу данных новое знаничение приватного ключа пользователя.

        :param str username: имя пользователя
        :param str private_key: приватный ключ
        :return: None
        """
        user = self.session.query(
            self.Users).filter_by(
            username=username).first()
        user.private_key = private_key
        self.session.commit()

    def get_user_history(self, username, target_username):
        """
        Возвращает историю всех сообщений пользователя

        :param str username: имя пользователя
        :param str target_username: имя пользователя-контакта
        :return: кортеж с сообщениями пользователя
        :rtype: tuple
        """
        query = self.session.query(
            self.Messages.sender,
            self.Messages.recipient,
            self.Messages.message,
            self.Messages.date).filter(
            ((self.Messages.sender == username) & (
                self.Messages.recipient == target_username) | (
                self.Messages.sender == target_username) & (
                    self.Messages.recipient == username))).order_by(
                        self.Messages.date)
        return query.all()

    def new_message_add(self, sender, recipient, message, date):
        """
        Добавляет новое сообщение одного пользователя к другому.

        :param str sender: имя отправителя
        :param str recipient: имя получателя
        :param str message: текст сообщения
        :param DateTime date: дата сообщения
        :return: None
        """
        self.session.add(self.Messages(sender, recipient, message, date))
        self.session.commit()

    def get_user_contacts(self, username):
        """
        Возвращает список контактов пользователя.

        :param str username: имя пользователя
        :return: кортех со списком контактов
        :rtype: tuple
        """

        user = self.session.query(
            self.Users).filter_by(
            username=username).first()
        return tuple(
            chain(
                *
                self.session.query(
                    self.Contacts.contact_username).filter_by(
                    user=user.id).all()))

    def add_contact(self, username, target_username):
        """
        Добавляет нового пользователя в список контактов

        :param str username: имя пользователя
        :param str target_username: имя пользователя-контакта
        :return: None
        """

        if target_username not in self.get_user_contacts(username):
            user = self.session.query(
                self.Users).filter_by(
                username=username).first()
            self.session.add(self.Contacts(user.id, target_username))
            self.session.commit()

    def delete_contact(self, username, target_username):
        """
        Удаляет контакт из списка контактов

        :param str username: имя пользователя
        :param str target_username: имя пользователя-контакта
        :return: None
        """
        user = self.session.query(
            self.Users).filter_by(
            username=username).first()
        self.session.query(self.Contacts).filter(
            (self.Contacts.user == user.id) &
            (self.Contacts.contact_username == target_username)
        ).delete()
        self.session.commit()
