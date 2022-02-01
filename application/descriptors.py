import logging
import re

LOG = logging.getLogger("server_logger")


class Port:
	def __set__(self, instance, value):
		if not 1023 < value < 65536:
			LOG.critical(f"Wrong port: {value}")
			raise ValueError
		instance.__dict__[self.name] = value

	def __set_name__(self, owner, name):
		self.name = name


class Address:
	def __set__(self, instance, value):
		if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", value) is None:
			LOG.critical(f"Wrong address: {value}")
			raise ValueError
		instance.__dict__[self.name] = value

	def __set_name__(self, owner, name):
		self.name = name
