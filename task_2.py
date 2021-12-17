word_list = [b"class", b"function", b"method"]

def words_info(words):
	for i in words:
		print(i)
		print(type(i))
		print(len(i))

words_info(word_list)