word_list = ["разработка", "администрирование", "protocol", "standard"]

def encode_decode(words):
	for i in words:
		encoded = i.encode()
		print(encoded)
		decoded = encoded.decode()
		print(decoded)
		print()

encode_decode(word_list)