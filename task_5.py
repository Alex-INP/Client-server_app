import chardet
import subprocess

addresses = ["yandex.ru", "youtube.com"]

def ping_address(address):
	proccess = subprocess.Popen(["ping", address], stdout=subprocess.PIPE)

	for i in proccess.stdout:
		chardet_data = chardet.detect(i)
		print(i.decode(chardet_data["encoding"]).encode("utf-8").decode("utf-8"))

for i in addresses:
	ping_address(i)