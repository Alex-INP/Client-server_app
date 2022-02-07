import datetime
import sqlalchemy as sqla
from sqlalchemy.orm import mapper, sessionmaker


class Storage:
	class Users:
		def __init__(self, username):
			self.name = username
			self.last_login = datetime.datetime.now()
			self.id = None


	class ActiveUsers:
		def __init__(self, user_id, ip_address, port, login_time):
			self.user = user_id
			self.ip_address = ip_address
			self.port = port
			self.login_time = login_time
			self.id = None


	class LoginHistory:
		def __init__(self, name, date, ip, port):
			self.id = None
			self.name = name
			self.date = date
			self.ip_address = ip
			self.port = port

	def __init__(self):
		self.engine = sqla.create_engine("sqlite:///server_db.db3", echo=False, pool_recycle=7200)
		self.metadata = sqla.MetaData()

		users_table = sqla.Table("Users", self.metadata,
								 sqla.Column("id", sqla.Integer, primary_key=True),
								 sqla.Column("name", sqla.String, unique=True),
								 sqla.Column("last_login", sqla.DateTime)
								 )
		active_users_table = sqla.Table("Active_users", self.metadata,
										sqla.Column("id", sqla.Integer, primary_key=True),
										sqla.Column("user", sqla.ForeignKey("Users.id"), unique=True),
										sqla.Column("ip_address", sqla.String),
										sqla.Column("port", sqla.String),
										sqla.Column("login_time", sqla.DateTime)
										)
		login_history = sqla.Table("Login_history", self.metadata,
								   sqla.Column("id", sqla.Integer, primary_key=True),
								   sqla.Column("name", sqla.ForeignKey("Users.id")),
								   sqla.Column("date", sqla.DateTime),
								   sqla.Column("ip_address", sqla.String),
								   sqla.Column("port", sqla.String),
								   )

		self.metadata.create_all(self.engine)

		mapper(self.Users, users_table)
		mapper(self.ActiveUsers, active_users_table)
		mapper(self.LoginHistory, login_history)

		SESSION = sessionmaker(self.engine)
		self.session = SESSION()

		self.session.query(self.ActiveUsers).delete()
		self.session.commit()

	def user_login(self, username, ip_address, port):
		query = self.session.query(self.Users).filter_by(name=username)
		if query.count():
			user = query.first()
			user.last_login = datetime.datetime.now()
		else:

			user = self.Users(username)

			self.session.add(user)
			self.session.commit()

		active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
		self.session.add(active_user)

		history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
		self.session.add(history)

		self.session.commit()

	def user_logout(self, username):
		user = self.session.query(self.Users).filter_by(name=username).first()
		self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
		self.session.commit()

	def users_list(self):
		return self.session.query(self.Users.name, self.Users.last_login).all()

	def active_users_list(self):
		query = self.session.query(self.Users.name,
								   self.ActiveUsers.ip_address,
								   self.ActiveUsers.port,
								   self.ActiveUsers.login_time
								   ).join(self.Users)
		return query.all()

	def login_history(self, username=None):
		query = self.session.query(self.Users.name,
								   self.LoginHistory.date,
								   self.LoginHistory.ip_address,
								   self.LoginHistory.port,
								   ).join(self.Users)
		if username:
			query = query.filter(self.Users.name == username)
		return query.all()


if __name__ == '__main__':
	test_db = Storage()

	test_db.user_login('client_1', '192.168.1.4', 8888)
	test_db.user_login('client_2', '192.168.1.5', 7777)

	print(test_db.active_users_list())

	test_db.user_logout('client_1')

	print(test_db.active_users_list())

	test_db.login_history('client_1')

	print(test_db.users_list())
