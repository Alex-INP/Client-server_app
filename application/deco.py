# import log.client_log_config
# import log.server_log_config
import inspect
import logging


def log(func):
	def wrapper(*args, **kwargs):
		module_name = inspect.stack()[1][1].split("/")[-1][:-3]
		if module_name == "server":
			LOG = logging.getLogger("server_logger")
		elif module_name == "client":
			LOG = logging.getLogger("client_logger")
		LOG.debug(f"Function name: {func.__name__}, Args: {args}, Kwargs: {kwargs}", stacklevel=2)
		return func(*args, **kwargs)
	return wrapper
