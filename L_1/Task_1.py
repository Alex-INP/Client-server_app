import subprocess
import chardet
import re

def host_ping(addresses):
	results = {"Availiable address": [], "Not avaliable address": []}
	for i in addresses:
		prc = subprocess.Popen(f"ping {i}", stdout=subprocess.PIPE)
		prc.wait()
		data_enc = prc.stdout.read()
		data_dec = data_enc.decode(chardet.detect(data_enc)["encoding"])

		if prc.returncode == 0 and not re.search(r"Заданный узел недоступен", data_dec):
			results["Availiable address"].append(i)
		else:
			results["Not avaliable address"].append(i)
	return results

if __name__ == "__main__":
	adr = ["www.youtube.com", "www.yandex.ru", "www.sdfsdf.ru", "www.google.com", "192.168.0.1"]
	print(host_ping(adr))