import logging
import os

log = logging.getLogger("client_logger")
log.setLevel(logging.DEBUG)

log_msg_format = logging.Formatter(f"%(asctime)-15s %(levelname)-10s %(module)-10s %(message)s")

log_handler = logging.FileHandler(os.path.join(os.getcwd(), "log/client_log.log"), encoding="utf-8")
log_handler.setFormatter(log_msg_format)

log.addHandler(log_handler)

if __name__ == "__main__":
	log.critical("My critical message")
	log.error("My error message")
	log.warning("My warning message")
	log.info("My info message")
	log.debug("My debug message")