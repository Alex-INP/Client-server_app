word_list = ["attribute", "класс", "функция", "type"]

def asci_bytes_convert(words):
	for i in words:
		try:
			print(bytes(i, "ascii"))
		except:
			print(f"Can't be converted: '{i}'")

asci_bytes_convert(word_list)