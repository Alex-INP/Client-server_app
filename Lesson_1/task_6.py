import chardet

with open("test_file.txt", "rb") as file:
	content = file.read()
	chardet_data = chardet.detect(content)
	print(f"Encoding: {chardet_data['encoding']}")
	print(content.decode(chardet_data['encoding']).encode("utf-8").decode("utf-8"))
